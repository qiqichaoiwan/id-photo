"""WeChat virtual-goods checkout. Production checkout remains opt-in."""
import asyncio
import base64
import calendar
import hashlib
import hmac
import json
import logging
import os
import secrets
import struct
import threading
import time
from datetime import datetime, timedelta, timezone

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse, JSONResponse

from miniapp_identity import get_openid
from miniapp_membership import database, subject_for
from miniapp_security import exchange_wechat_code

LOG = logging.getLogger('idphoto.payment')
router = APIRouter()
CHINA = timezone(timedelta(hours=8))
_token_lock = threading.Lock()
_token_value = ''
_token_expires = 0.0


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def payment_enabled():
    return os.environ.get('IDPHOTO_PAYMENT_ENABLED', 'false').lower() == 'true'


def payment_env():
    value = os.environ.get('IDPHOTO_PAYMENT_ENV', '0')
    if value not in ('0', '1'):
        raise RuntimeError('IDPHOTO_PAYMENT_ENV 必须为 0 或 1')
    if value == '1':
        from pathlib import Path
        from miniapp_membership import DATA_DIR
        if DATA_DIR.resolve() != (Path(__file__).resolve().parent / '.miniapp_sandbox').resolve():
            raise RuntimeError('沙箱支付必须使用独立的沙箱数据库')
    return int(value)


def required(name):
    value = os.environ.get(name, '')
    if not value:
        raise HTTPException(503, '支付服务尚未完成配置')
    return value


def validate_payment_config():
    payment_env()
    if not payment_enabled():
        return
    for field in ('WECHAT_APP_ID', 'WECHAT_APP_SECRET', 'WECHAT_OFFER_ID', 'WECHAT_PAY_APP_KEY', 'WECHAT_PUSH_TOKEN', 'WECHAT_PUSH_AES_KEY'):
        required(field)
    if len(decode_push_key()) != 32:
        raise RuntimeError('微信推送密钥无效')


def pay_sig(uri, body):
    return hmac.new(required('WECHAT_PAY_APP_KEY').encode(), (uri + '&' + body).encode(), hashlib.sha256).hexdigest()


def wechat_access_token():
    global _token_value, _token_expires
    with _token_lock:
        if _token_value and time.monotonic() < _token_expires:
            return _token_value
        try:
            response = requests.get('https://api.weixin.qq.com/cgi-bin/token', params={
                'grant_type': 'client_credential', 'appid': required('WECHAT_APP_ID'), 'secret': required('WECHAT_APP_SECRET')}, timeout=8)
            response.raise_for_status()
            data = response.json()
            token = data.get('access_token')
            lifetime = int(data.get('expires_in', 0))
            if not isinstance(token, str) or not token or lifetime < 120:
                raise ValueError('invalid token response')
            _token_value, _token_expires = token, time.monotonic() + lifetime - 120
            return token
        except (requests.RequestException, ValueError, TypeError):
            raise HTTPException(503, '微信订单服务暂不可用')


def plus_calendar_months(value, months):
    local = value.astimezone(CHINA)
    count = local.year * 12 + local.month - 1 + months
    year, month0 = divmod(count, 12)
    month = month0 + 1
    return local.replace(year=year, month=month, day=min(local.day, calendar.monthrange(year, month)[1])).astimezone(timezone.utc)


def grant_order(order_no, wx_order_id=None, needs_ack=False):
    # A signed delivery message can omit WeChatPayInfo for Apple payments.
    # The business order is always unique; bind the WeChat ID when available.
    if wx_order_id is not None and (not isinstance(wx_order_id, str) or not wx_order_id or len(wx_order_id) > 128):
        raise ValueError('invalid platform order id')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM orders WHERE order_no = ?', (order_no,)).fetchone()
        if not row:
            raise ValueError('unknown order')
        if wx_order_id and row['platform_order_id'] and row['platform_order_id'] != wx_order_id:
            raise ValueError('platform order mismatch')
        if wx_order_id:
            other = db.execute('SELECT order_no FROM orders WHERE platform_order_id = ? AND order_no != ?', (wx_order_id, order_no)).fetchone()
            if other:
                raise ValueError('platform order already bound')
        grant = db.execute('SELECT order_no FROM membership_grants WHERE order_no = ?', (order_no,)).fetchone()
        if grant:
            if wx_order_id and not row['platform_order_id']:
                db.execute('UPDATE orders SET platform_order_id = ?, updated_at = ? WHERE order_no = ?', (wx_order_id, now_iso(), order_no))
            if needs_ack:
                db.execute('UPDATE orders SET notify_needed = 1, updated_at = ? WHERE order_no = ?', (now_iso(), order_no))
            return
        if row['status'] != 'pending' or row['review_needed']:
            raise ValueError('order cannot be granted')
        current = datetime.now(timezone.utc)
        existing = db.execute('SELECT expires_at FROM members WHERE subject = ?', (row['subject'],)).fetchone()
        previous = datetime.fromisoformat(existing['expires_at'].replace('Z', '+00:00')) if existing else current
        if previous.tzinfo is None:
            raise ValueError('invalid existing expiry')
        start = max(current, previous)
        expiry = plus_calendar_months(start, row['months'])
        db.execute('INSERT INTO membership_grants (order_no, subject, start_at, expires_at, created_at) VALUES (?, ?, ?, ?, ?)',
                   (order_no, row['subject'], start.isoformat(), expiry.isoformat(), current.isoformat()))
        db.execute('INSERT INTO members (subject, expires_at) VALUES (?, ?) ON CONFLICT(subject) DO UPDATE SET expires_at = excluded.expires_at',
                   (row['subject'], expiry.isoformat()))
        db.execute("UPDATE orders SET status = 'paid', platform_order_id = ?, expires_at = ?, updated_at = ?, notify_needed = ? WHERE order_no = ?",
                   (wx_order_id, expiry.isoformat(), current.isoformat(), int(needs_ack), order_no))


class OrderInput(BaseModel):
    plan_id: int = Field(ge=1)
    code: str = Field(min_length=1, max_length=256)
    price_fen: int = Field(ge=1)
    months: int = Field(ge=1, le=120)


@router.post('/membership/orders')
async def create_order(data: OrderInput, request: Request):
    if not payment_enabled():
        raise HTTPException(503, '会员购买尚未开放')
    validate_payment_config()
    user_id = subject_for(request)
    current_openid = await asyncio.to_thread(get_openid, user_id)
    login = await exchange_wechat_code(data.code)
    if not hmac.compare_digest(login['openid'], current_openid):
        raise HTTPException(401, '微信账号已变更，请重新登录')
    session_key = login.get('session_key')
    if not isinstance(session_key, str) or not session_key:
        raise HTTPException(401, '微信登录已过期，请重试')
    order_no = ('S' if payment_env() else 'M') + secrets.token_hex(15)
    attach = secrets.token_hex(16)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        plan = db.execute("SELECT * FROM plans WHERE id = ? AND status = 'active'", (data.plan_id,)).fetchone()
        if not plan or not plan['wechat_product_id']:
            raise HTTPException(409, '该套餐尚未开放购买')
        if plan['price_fen'] != data.price_fen or plan['months'] != data.months:
            raise HTTPException(409, '套餐信息已变化，请返回重新确认')
        pending = db.execute("SELECT * FROM orders WHERE subject = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()
        if pending:
            if (pending['review_needed'] or pending['plan_id'] != plan['id'] or pending['price_fen'] != plan['price_fen']
                    or pending['months'] != plan['months'] or pending['product_id'] != plan['wechat_product_id']):
                raise HTTPException(409, '您有一笔订单正在确认，请先到购买记录查看')
            # Reuse the same business order after cancel/network interruption.
            order_no, attach = pending['order_no'], pending['attach']
        else:
            created = now_iso()
            db.execute("INSERT INTO orders (order_no, subject, plan_id, plan_name, months, price_fen, status, created_at, updated_at, product_id, attach) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)",
                       (order_no, user_id, plan['id'], plan['name'], plan['months'], plan['price_fen'], created, created, plan['wechat_product_id'], attach))
        sign_data = json.dumps({'offerId': required('WECHAT_OFFER_ID'), 'buyQuantity': 1, 'env': payment_env(),
                                'currencyType': 'CNY', 'productId': plan['wechat_product_id'],
                                'goodsPrice': plan['price_fen'], 'outTradeNo': order_no, 'attach': attach}, ensure_ascii=False, separators=(',', ':'))
        result = {'order_no': order_no, 'pay_data': {'mode': 'short_series_goods', 'signData': sign_data,
                  'paySig': pay_sig('requestVirtualPayment', sign_data),
                  'signature': hmac.new(session_key.encode(), sign_data.encode(), hashlib.sha256).hexdigest()}}
    return result


def notify_platform_delivered(order_no):
    body = {'order_id': order_no, 'env': payment_env()}
    try:
        response = requests.post('https://api.weixin.qq.com/xpay/notify_provide_goods',
                                 params={'access_token': wechat_access_token()}, json=body, timeout=8)
        response.raise_for_status()
        result = response.json() if response.content else {}
        if not isinstance(result, dict) or (result and result.get('errcode') != 0):
            raise ValueError('delivery acknowledgment failed')
    except (requests.RequestException, ValueError, HTTPException):
        LOG.warning('微信发货状态通知暂不可用，稍后重试')
        return
    with database() as db:
        db.execute('UPDATE orders SET notify_needed = 0, updated_at = ? WHERE order_no = ?', (now_iso(), order_no))


def mark_order_review(order_no, reason):
    event_record({'Event': 'order_verification', 'OrderNo': order_no, 'Reason': reason},
                 order_no, 'manual_review', reason)


def query_platform_order(order_no):
    with database() as db:
        row = db.execute('SELECT * FROM orders WHERE order_no = ?', (order_no,)).fetchone()
        if not row:
            raise HTTPException(404, '订单不存在')
        order = dict(row)
    if not order['product_id']:
        return
    openid = get_openid(order['subject'])
    body = json.dumps({'openid': openid, 'env': payment_env(), 'order_id': order_no}, separators=(',', ':'))
    try:
        response = requests.post('https://api.weixin.qq.com/xpay/query_order', params={
            'access_token': wechat_access_token(), 'pay_sig': pay_sig('/xpay/query_order', body)},
            data=body.encode(), headers={'Content-Type': 'application/json'}, timeout=8)
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        raise HTTPException(503, '微信订单查询暂不可用')
    if result.get('errcode') != 0 or not isinstance(result.get('order'), dict):
        raise HTTPException(503, '订单确认中，请稍后重试')
    remote = result['order']
    if remote.get('order_id') != order_no or remote.get('order_type') not in (0, 7) or remote.get('env_type') != payment_env() + 1:
        mark_order_review(order_no, '微信订单标识、类型或环境不一致')
        raise HTTPException(503, '订单信息待核对')
    status = remote.get('status')
    if status in (2, 4):
        if remote.get('order_fee') != order['price_fen'] or remote.get('paid_fee') != order['price_fen']:
            mark_order_review(order_no, '微信订单金额与下单快照不一致')
            raise HTTPException(503, '订单金额待核对')
        if not isinstance(remote.get('wx_order_id'), str) or not remote['wx_order_id']:
            raise HTTPException(503, '订单信息待核对')
        try:
            grant_order(order_no, remote.get('wx_order_id'), needs_ack=(status == 2))
        except (ValueError, TypeError):
            mark_order_review(order_no, '微信订单发放状态冲突')
            raise HTTPException(503, '订单信息待人工核对')
        channel_id = remote.get('channel_order_id')
        if isinstance(channel_id, str) and 0 < len(channel_id) <= 128:
            with database() as db:
                db.execute('UPDATE orders SET channel_order_id = ? WHERE order_no = ?', (channel_id, order_no))
        if status == 2:
            notify_platform_delivered(order_no)
        else:
            with database() as db:
                db.execute('UPDATE orders SET notify_needed = 0, updated_at = ? WHERE order_no = ?', (now_iso(), order_no))
    elif status == 6:
        with database() as db:
            db.execute("UPDATE orders SET status = 'closed', updated_at = ? WHERE order_no = ? AND status = 'pending'", (now_iso(), order_no))
    elif status in (5, 8):
        mark_order_review(order_no, '微信订单显示退款状态，需人工核对')


@router.post('/membership/orders/{order_no}/refresh')
def refresh_order(order_no: str, request: Request):
    user_id = subject_for(request)
    with database() as db:
        row = db.execute('SELECT order_no FROM orders WHERE order_no = ? AND subject = ?', (order_no, user_id)).fetchone()
    if not row:
        raise HTTPException(404, '订单不存在')
    query_platform_order(order_no)
    with database() as db:
        row = db.execute('SELECT order_no, plan_name, months, price_fen, status, created_at, expires_at, review_needed FROM orders WHERE order_no = ? AND subject = ?', (order_no, user_id)).fetchone()
    return dict(row)


def decode_push_key():
    try:
        return base64.b64decode(required('WECHAT_PUSH_AES_KEY') + '=', validate=True)
    except (ValueError, TypeError):
        raise HTTPException(503, '微信消息推送尚未配置')


def push_signature(*parts):
    return hashlib.sha1(''.join(sorted(parts)).encode()).hexdigest()


def decrypt_message(encrypted):
    key = decode_push_key()
    try:
        raw = base64.b64decode(encrypted, validate=True)
        dec = Cipher(algorithms.AES(key), modes.CBC(key[:16])).decryptor()
        padded = dec.update(raw) + dec.finalize()
        padding = padded[-1]
        if padding < 1 or padding > 32 or padded[-padding:] != bytes([padding]) * padding:
            raise ValueError('invalid padding')
        plain = padded[:-padding]
        length = struct.unpack('!I', plain[16:20])[0]
        if length > len(plain) - 20:
            raise ValueError('invalid length')
        message, appid = plain[20:20 + length], plain[20 + length:]
        if not hmac.compare_digest(appid, required('WECHAT_APP_ID').encode()):
            raise ValueError('invalid appid')
        result = json.loads(message.decode('utf-8'))
        if not isinstance(result, dict):
            raise ValueError('invalid body')
        return result
    except (ValueError, IndexError, TypeError, UnicodeError, struct.error):
        raise HTTPException(400, '微信消息无效')


def encrypt_reply(value, timestamp, nonce):
    key = decode_push_key()
    message = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    raw = secrets.token_bytes(16) + struct.pack('!I', len(message)) + message + required('WECHAT_APP_ID').encode()
    count = 32 - len(raw) % 32
    enc = Cipher(algorithms.AES(key), modes.CBC(key[:16])).encryptor()
    encrypted = base64.b64encode(enc.update(raw + bytes([count]) * count) + enc.finalize()).decode()
    return {'Encrypt': encrypted, 'MsgSignature': push_signature(required('WECHAT_PUSH_TOKEN'), timestamp, nonce, encrypted), 'TimeStamp': timestamp, 'Nonce': nonce}


@router.get('/payment/notify')
def verify_push(signature: str = '', timestamp: str = '', nonce: str = '', echostr: str = ''):
    if (not all((signature, timestamp, nonce, echostr)) or len(signature) != 40
            or len(timestamp) > 20 or len(nonce) > 128 or len(echostr) > 1024
            or not hmac.compare_digest(signature, push_signature(required('WECHAT_PUSH_TOKEN'), timestamp, nonce))):
        raise HTTPException(403, '签名无效')
    return PlainTextResponse(echostr)


def event_record(event, order_no, state, details=''):
    stable = {key: value for key, value in event.items() if key not in ('RetryTimes', 'CreateTime')}
    fingerprint = hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    with database() as db:
        db.execute('INSERT OR IGNORE INTO payment_events (event_key, order_no, event_type, state, created_at, details) VALUES (?, ?, ?, ?, ?, ?)',
                   (fingerprint, order_no, str(event.get('Event', ''))[:80], state, now_iso(), details[:300]))
        if state == 'manual_review':
            stored = db.execute('SELECT order_no, state FROM payment_events WHERE event_key = ?', (fingerprint,)).fetchone()
            if stored and stored['state'] == 'manual_review':
                matched = stored['order_no'] or order_no
                if matched and not stored['order_no']:
                    db.execute('UPDATE payment_events SET order_no = ? WHERE event_key = ?', (matched, fingerprint))
                if matched:
                    db.execute('UPDATE orders SET review_needed = 1, updated_at = ? WHERE order_no = ?', (now_iso(), matched))


def deliver_event(event, order_no):
    with database() as db:
        row = db.execute('SELECT * FROM orders WHERE order_no = ?', (order_no,)).fetchone()
        order = dict(row) if row else None
    info = event.get('GoodsInfo')
    if not order or not isinstance(info, dict):
        raise HTTPException(400, '订单信息不匹配')
    if (event.get('OpenId') != get_openid(order['subject']) or str(event.get('Env')) != str(payment_env())
            or info.get('ProductId') != order['product_id'] or info.get('Quantity') != 1
            or info.get('OrigPrice') != order['price_fen'] or info.get('ActualPrice') != order['price_fen']
            or info.get('Attach') != order['attach']):
        raise HTTPException(400, '订单信息不匹配')
    try:
        # WeChatPayInfo is optional for Apple; the signed OutTradeNo plus the
        # immutable order snapshot identifies this delivery idempotently.
        grant_order(order_no)
    except ValueError:
        event_record(event, order_no, 'manual_review', '发货状态冲突，请人工核对微信订单')
        raise HTTPException(409, '订单信息待核对')
    event_record(event, order_no, 'delivered')


def refund_event(event):
    # Different payment channels supply different IDs. Only associate an event
    # when all matching identifiers identify one order and the OpenID agrees.
    candidates = {}
    with database() as db:
        for field, column in (('MchOrderId', 'order_no'), ('MchOrderId', 'channel_order_id'),
                              ('WxOrderId', 'platform_order_id'), ('Attach', 'attach')):
            value = event.get(field)
            if isinstance(value, str) and value and len(value) <= 128:
                for row in db.execute(f'SELECT order_no, subject FROM orders WHERE {column} = ?', (value,)).fetchall():
                    candidates[row['order_no']] = row['subject']
    order_no = ''
    if len(candidates) == 1:
        candidate, subject = next(iter(candidates.items()))
        if isinstance(event.get('OpenId'), str) and hmac.compare_digest(event['OpenId'], get_openid(subject)):
            order_no = candidate
    state = 'manual_review' if str(event.get('RetCode')) == '0' else 'refund_failed'
    parts = ['退款成功，需人工核对' if state == 'manual_review' else '退款未确认成功']
    for field, label in (('WxRefundId', '微信退款号'), ('MchRefundId', '商户退款号'),
                         ('WxOrderId', '微信订单号'), ('MchOrderId', '商户订单号'), ('RefundFee', '退款金额(分)')):
        value = event.get(field)
        if isinstance(value, (str, int)) and str(value):
            parts.append(f'{label}: {str(value)[:80]}')
    event_record(event, order_no, state, '；'.join(parts))


@router.post('/payment/notify')
async def receive_push(request: Request, background_tasks: BackgroundTasks, timestamp: str = '', nonce: str = '', msg_signature: str = '', encrypt_type: str = ''):
    if (encrypt_type != 'aes' or not all((timestamp, nonce, msg_signature)) or len(timestamp) > 20
            or len(nonce) > 128 or len(msg_signature) != 40):
        raise HTTPException(403, '请使用安全模式')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise HTTPException(413, '消息过大')
    try:
        envelope = json.loads(body)
        encrypted = envelope['Encrypt']
        if not isinstance(encrypted, str):
            raise ValueError('invalid ciphertext')
    except (ValueError, KeyError, TypeError):
        raise HTTPException(400, '微信消息无效')
    expected = push_signature(required('WECHAT_PUSH_TOKEN'), timestamp, nonce, encrypted)
    if not hmac.compare_digest(msg_signature, expected):
        raise HTTPException(403, '签名无效')
    event = decrypt_message(encrypted)
    event_type = event.get('Event')
    order_no = str(event.get('OutTradeNo') or event.get('pay_order_id') or '')[:128]
    if event_type == 'xpay_goods_deliver_notify' and str(event.get('Env')) == '1' and payment_env() == 0:
        # The platform has one push URL. Forward signed sandbox envelopes only
        # to the loopback sandbox service, which verifies them again and uses a
        # separate database. No sandbox grant can affect production members.
        def forward_sandbox():
            try:
                response = requests.post('http://127.0.0.1:8093/sandbox/payment/notify',
                    params={'timestamp': timestamp, 'nonce': nonce, 'msg_signature': msg_signature, 'encrypt_type': encrypt_type},
                    data=bytes(body), headers={'Content-Type': 'application/json'}, timeout=(1, 5))
                if response.status_code != 200 or response.text.strip() != 'success':
                    raise ValueError('sandbox receiver unavailable')
            except (requests.RequestException, ValueError):
                raise HTTPException(503, '沙箱消息接收服务暂不可用')
        await asyncio.to_thread(forward_sandbox)
        return PlainTextResponse('success')
    if event_type == 'xpay_goods_deliver_notify':
        await asyncio.to_thread(deliver_event, event, order_no)
    elif event_type == 'xpay_refund_notify':
        # The owner chose manual review for refunds; no entitlement is removed here.
        await asyncio.to_thread(refund_event, event)
    elif event_type == 'xpay_subscribe_ios_refund_query_notify':
        # Reply first: Apple requires a decision within three seconds.
        background_tasks.add_task(event_record, event, order_no, 'refund_inquiry', '按商家规则建议退款，最终决定由 Apple 作出')
        reply = {'ErrCode': 0, 'ErrMsg': 'success', 'IosRefundQueryResponse': {
            'result_code': 0, 'result_info': '建议退款', 'evidence': '商家对会员退款申请采取默认建议同意的处理规则，退款结果以 Apple 最终决定为准。'}}
        return JSONResponse(encrypt_reply(reply, timestamp, nonce))
    else:
        await asyncio.to_thread(event_record, event, order_no, 'unhandled')
    return PlainTextResponse('success')


def reconcile_loop(stop):
    while not stop.wait(300):
        if not os.environ.get('WECHAT_PAY_APP_KEY'):
            continue
        try:
            with database() as db:
                rows = db.execute("SELECT order_no FROM orders WHERE product_id != '' AND (status = 'pending' OR (status = 'paid' AND (platform_order_id IS NULL OR notify_needed = 1))) ORDER BY updated_at LIMIT 100").fetchall()
            for row in rows:
                if stop.is_set():
                    return
                try:
                    query_platform_order(row['order_no'])
                except Exception:
                    LOG.warning('会员订单查单暂不可用，稍后重试')
                finally:
                    with database() as db:
                        db.execute('UPDATE orders SET updated_at = ? WHERE order_no = ?', (now_iso(), row['order_no']))
        except Exception:
            LOG.warning('会员订单补偿任务暂不可用')
