"""Admin-initiated WeChat virtual-payment refunds.

An accepted request is not a completed refund. Ambiguous results remain locked
until an administrator checks the platform and records the outcome.
"""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timezone

import requests
from fastapi import HTTPException
from pydantic import BaseModel, Field, conint, validator
from typing import Literal

from miniapp_identity import get_openid
from miniapp_membership import database
from miniapp_payment import now_iso, pay_sig, payment_env, wechat_access_token

OPEN_STATES = ('dispatching', 'accepted', 'unknown', 'notice_success', 'notice_failed')
PUBLIC_FIELDS = '''refund_id, order_no, amount_fen, left_fee_before, reason_code,
    note, state, wx_refund_id, platform_code, detail, query_status, query_checked_at, created_at, updated_at'''


class RefundInput(BaseModel):
    request_key: str = Field(min_length=32, max_length=32)
    amount_fen: conint(strict=True, gt=0, le=10000000)
    expected_left_fen: conint(strict=True, gt=0, le=10000000)
    reason_code: Literal['0', '1', '2', '3', '4', '5']
    note: str = Field(min_length=2, max_length=200)

    @validator('request_key')
    def valid_request_key(cls, value):
        if not re.fullmatch(r'[a-f0-9]{32}', value):
            raise ValueError('退款请求编号无效')
        return value

    @validator('note')
    def valid_note(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError('请填写退款说明')
        return value


class RefundReviewInput(BaseModel):
    outcome: Literal['confirmed', 'not_refunded']
    note: str = Field(min_length=2, max_length=200)

    @validator('note')
    def valid_note(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError('请填写平台核对记录')
        return value


def _order(order_no):
    with database() as db:
        row = db.execute('SELECT * FROM orders WHERE order_no=?', (order_no,)).fetchone()
        if not row:
            raise HTTPException(404, '订单不存在')
        active = db.execute("SELECT " + PUBLIC_FIELDS + " FROM refund_transactions WHERE order_no=? AND state NOT IN ('confirmed','not_refunded') LIMIT 1", (order_no,)).fetchone()
        return dict(row), dict(active) if active else None


def _query_payment_order(order):
    openid = get_openid(order['subject'])
    body = json.dumps({'openid': openid, 'env': payment_env(), 'order_id': order['order_no']}, separators=(',', ':'))
    try:
        response = requests.post('https://api.weixin.qq.com/xpay/query_order',
                                 params={'access_token': wechat_access_token(), 'pay_sig': pay_sig('/xpay/query_order', body)},
                                 data=body.encode(), headers={'Content-Type': 'application/json'}, timeout=8)
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError, TypeError):
        raise HTTPException(503, '微信订单查询暂不可用，请稍后重试')
    if not isinstance(result, dict) or result.get('errcode') != 0 or not isinstance(result.get('order'), dict):
        raise HTTPException(503, '微信订单查询未完成，请稍后重试')
    remote = result['order']
    if (remote.get('order_id') != order['order_no'] or type(remote.get('order_type')) is not int
            or remote['order_type'] not in (0, 7) or remote.get('env_type') != payment_env() + 1):
        raise HTTPException(409, '微信订单标识、渠道或环境不匹配，请人工核对')
    return remote


def _prepare_quote(order_no):
    order, active = _order(order_no)
    if not order['product_id'] or order['status'] != 'paid':
        raise HTTPException(409, '仅能为已支付并关联微信商品的订单核对退款')
    remote = _query_payment_order(order)
    if remote['order_type'] == 7:
        return order, {'order_no': order_no, 'channel': 'ios', 'eligible': False,
                       'message': '此订单为 Apple 内购，请引导用户向 Apple 申请退款', 'active_refund': active}
    platform_id = remote.get('wx_order_id')
    left = remote.get('left_fee')
    if (not isinstance(platform_id, str) or not 0 < len(platform_id) <= 128
            or (order['platform_order_id'] and not hmac.compare_digest(platform_id, order['platform_order_id']))
            or type(remote.get('order_fee')) is not int or type(remote.get('paid_fee')) is not int
            or remote['order_fee'] != order['price_fen'] or remote['paid_fee'] != order['price_fen']
            or type(left) is not int or left < 0 or left > order['price_fen']):
        raise HTTPException(409, '微信订单金额或编号不匹配，请人工核对')
    message = ''
    if active:
        message = '已有退款待核对，请先查看该退款记录'
    elif order['review_needed']:
        message = '该订单有待核对的支付事件，请先处理'
    elif type(remote.get('status')) is not int or remote['status'] not in (2, 4):
        message = '微信订单状态不支持在此发起退款，请前往微信后台核对'
    elif left == 0:
        message = '微信显示当前没有可退金额'
    return order, {'order_no': order_no, 'channel': 'wechat', 'eligible': not message, 'message': message,
                   'paid_fen': order['price_fen'], 'left_fee': left, 'wx_order_id': platform_id,
                   'active_refund': active}


def refund_quote(order_no):
    return _prepare_quote(order_no)[1]


def _same_request(row, order_no, data):
    return (row['order_no'] == order_no and row['amount_fen'] == data.amount_fen
            and row['left_fee_before'] == data.expected_left_fen and row['reason_code'] == data.reason_code
            and row['note'] == data.note)


def _public_by_id(db, refund_id):
    row = db.execute('SELECT ' + PUBLIC_FIELDS + ' FROM refund_transactions WHERE refund_id=?', (refund_id,)).fetchone()
    return dict(row) if row else None


def _flag_membership_review(db, refund_id, order_no):
    """Keep refund verification separate from the administrator's entitlement decision."""
    event_key = hashlib.sha256(('admin-refund-review:' + refund_id).encode()).hexdigest()
    detail = f'后台退款单 {refund_id} 已确认或微信查单显示退款状态，请人工核对会员权益'
    db.execute('''INSERT OR IGNORE INTO payment_events(event_key,order_no,event_type,state,created_at,details)
                  VALUES (?,?,'order_verification','manual_review',?,?)''', (event_key, order_no, now_iso(), detail))
    event = db.execute('SELECT state FROM payment_events WHERE event_key=?', (event_key,)).fetchone()
    if event and event['state'] == 'manual_review':
        db.execute('UPDATE orders SET review_needed=1,updated_at=? WHERE order_no=?', (now_iso(), order_no))


def start_refund(order_no, data):
    with database() as db:
        previous = db.execute('SELECT * FROM refund_transactions WHERE request_key=?', (data.request_key,)).fetchone()
        if previous:
            if not _same_request(previous, order_no, data):
                raise HTTPException(409, '退款请求编号已被使用')
            return _public_by_id(db, previous['refund_id'])
    verified_order, quote = _prepare_quote(order_no)
    if not quote['eligible']:
        raise HTTPException(409, quote['message'])
    if data.expected_left_fen != quote['left_fee'] or data.amount_fen > quote['left_fee']:
        raise HTTPException(409, '可退金额已变化，请重新核对')
    refund_id = 'R' + secrets.token_hex(15)
    created = now_iso()
    try:
        with database() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM refund_transactions WHERE request_key=?', (data.request_key,)).fetchone()
            if previous:
                if not _same_request(previous, order_no, data):
                    raise HTTPException(409, '退款请求编号已被使用')
                return _public_by_id(db, previous['refund_id'])
            order = db.execute('SELECT * FROM orders WHERE order_no=?', (order_no,)).fetchone()
            active = db.execute("SELECT 1 FROM refund_transactions WHERE order_no=? AND state NOT IN ('confirmed','not_refunded')", (order_no,)).fetchone()
            if (not order or order['status'] != 'paid' or order['review_needed'] or active
                    or any(order[key] != verified_order[key] for key in ('subject', 'price_fen', 'product_id', 'platform_order_id'))):
                raise HTTPException(409, '订单状态已变化或已有退款待核对，请刷新')
            db.execute('''INSERT INTO refund_transactions
                (refund_id,order_no,request_key,amount_fen,left_fee_before,reason_code,note,pay_wx_order_id,state,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?, 'dispatching',?,?)''',
                (refund_id, order_no, data.request_key, data.amount_fen, data.expected_left_fen,
                 data.reason_code, data.note, quote['wx_order_id'], created, created))
            from miniapp_refund_entitlements import enqueue_check
            enqueue_check(db, order_no, refund_id, '', data.amount_fen, quote['wx_order_id'])
            db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                       ('start_refund', order_no, f'退款单 {refund_id}；金额 {data.amount_fen} 分；原因：{data.note}', created))
            subject = order['subject']
    except sqlite3.IntegrityError:
        raise HTTPException(409, '订单已有退款待核对，请刷新')

    # The ledger is committed before the network call. Never automatically
    # resend on timeout: the platform may already have accepted the request.
    try:
        body = json.dumps({'openid': get_openid(subject), 'order_id': order_no, 'refund_order_id': refund_id,
                           'left_fee': data.expected_left_fen, 'refund_fee': data.amount_fen,
                           'biz_meta': '', 'refund_reason': data.reason_code, 'req_from': '1',
                           'env': payment_env()}, ensure_ascii=False, separators=(',', ':'))
        response = requests.post('https://api.weixin.qq.com/xpay/refund_order',
                                 params={'access_token': wechat_access_token(), 'pay_sig': pay_sig('/xpay/refund_order', body)},
                                 data=body.encode(), headers={'Content-Type': 'application/json'}, timeout=8)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError('invalid refund response')
    except (requests.RequestException, ValueError, TypeError, HTTPException):
        result = None
    _record_dispatch_result(refund_id, result)
    with database() as db:
        return _public_by_id(db, refund_id)


def _record_dispatch_result(refund_id, result):
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM refund_transactions WHERE refund_id=?', (refund_id,)).fetchone()
        if not row:
            return
        code = result.get('errcode') if isinstance(result, dict) and type(result.get('errcode')) is int else None
        wx_id = result.get('refund_wx_order_id') if isinstance(result, dict) else None
        valid_success = (code == 0 and result.get('refund_order_id') == refund_id
                         and result.get('pay_order_id') == row['order_no']
                         and result.get('pay_wx_order_id') == row['pay_wx_order_id']
                         and isinstance(wx_id, str) and 0 < len(wx_id) <= 128)
        if valid_success and row['wx_refund_id'] and not hmac.compare_digest(row['wx_refund_id'], wx_id):
            valid_success = False
        if valid_success:
            state, detail = 'accepted', '微信已受理退款任务，最终结果需核对'
        elif code == 268490014:
            state, detail = 'accepted', '微信反馈退款处理中，最终结果需核对'
        else:
            state, detail = 'unknown', '退款结果未确认，请在微信后台核对后处理'
        # A verified callback may have arrived before the HTTP response.
        if row['state'] in ('notice_success', 'notice_failed') and (valid_success or code == 268490014 or result is None):
            state, detail = row['state'], row['detail']
        elif row['state'] not in OPEN_STATES:
            return
        stored_wx_id = row['wx_refund_id'] or (wx_id if valid_success else '')
        db.execute('UPDATE refund_transactions SET state=?,wx_refund_id=?,platform_code=?,detail=?,updated_at=? WHERE refund_id=?',
                   (state, stored_wx_id, code, detail, now_iso(), refund_id))


def record_refund_notice(event, matched_order):
    """Record a verified push only if its order, refund id and amount agree."""
    refund_id = event.get('MchRefundId')
    if not matched_order or not isinstance(refund_id, str) or not re.fullmatch(r'R[a-f0-9]{30}', refund_id):
        return
    amount, code, wx_id = event.get('RefundFee'), event.get('RetCode'), event.get('WxRefundId')
    if (str(event.get('Env')) != str(payment_env()) or type(amount) is not int
            or not isinstance(wx_id, str) or not 0 < len(wx_id) <= 128
            or type(code) is not int):
        return
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM refund_transactions WHERE refund_id=? AND order_no=?', (refund_id, matched_order)).fetchone()
        if not row or row['amount_fen'] != amount or row['state'] not in OPEN_STATES:
            return
        if event.get('MchOrderId') != row['order_no'] or event.get('WxOrderId') != row['pay_wx_order_id']:
            return
        if row['wx_refund_id'] and not hmac.compare_digest(row['wx_refund_id'], wx_id):
            return
        state = 'notice_success' if code == 0 else 'notice_failed'
        if row['state'] in ('notice_success', 'notice_failed') and row['state'] != state:
            state, detail = 'unknown', '退款通知结果冲突，请前往微信后台核对'
        else:
            detail = '微信通知退款成功，请核对退款单及会员权益' if code == 0 else '微信通知退款失败，请核对退款单'
        db.execute('UPDATE refund_transactions SET state=?,wx_refund_id=?,detail=?,updated_at=? WHERE refund_id=?',
                   (state, wx_id, detail, now_iso(), refund_id))


def refresh_refund(refund_id):
    """Read the refund order without turning a query response into a final outcome."""
    if not re.fullmatch(r'R[a-f0-9]{30}', refund_id):
        raise HTTPException(400, '退款单号无效')
    with database() as db:
        row = db.execute('''SELECT r.*, o.subject FROM refund_transactions r
                            JOIN orders o ON o.order_no=r.order_no WHERE r.refund_id=?''', (refund_id,)).fetchone()
        if not row:
            raise HTTPException(404, '退款记录不存在')
        snapshot = dict(row)
    body = json.dumps({'openid': get_openid(snapshot['subject']), 'env': payment_env(),
                       'order_id': refund_id}, separators=(',', ':'))
    try:
        response = requests.post('https://api.weixin.qq.com/xpay/query_order',
                                 params={'access_token': wechat_access_token(), 'pay_sig': pay_sig('/xpay/query_order', body)},
                                 data=body.encode(), headers={'Content-Type': 'application/json'}, timeout=8)
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError, TypeError):
        raise HTTPException(503, '退款单查询暂不可用，请到微信后台核对')
    remote = result.get('order') if isinstance(result, dict) and result.get('errcode') == 0 else None
    wx_id = remote.get('wx_order_id') if isinstance(remote, dict) else None
    status = remote.get('status') if isinstance(remote, dict) else None
    if (not isinstance(remote, dict) or remote.get('order_id') != refund_id
            or remote.get('order_type') != 1 or remote.get('env_type') != payment_env() + 1
            or type(remote.get('refund_fee')) is not int or remote['refund_fee'] != snapshot['amount_fen']
            or not isinstance(wx_id, str) or not 0 < len(wx_id) <= 128
            or (snapshot['wx_refund_id'] and not hmac.compare_digest(snapshot['wx_refund_id'], wx_id))
            or type(status) is not int or status not in range(11)):
        raise HTTPException(503, '微信退款单信息暂无法匹配，请到微信后台核对')
    checked = now_iso()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        current = db.execute('SELECT wx_refund_id FROM refund_transactions WHERE refund_id=?', (refund_id,)).fetchone()
        if not current or (current['wx_refund_id'] and not hmac.compare_digest(current['wx_refund_id'], wx_id)):
            raise HTTPException(409, '退款记录已变化，请刷新后核对')
        db.execute('UPDATE refund_transactions SET query_status=?,query_checked_at=?,wx_refund_id=?,updated_at=? WHERE refund_id=?',
                   (status, checked, current['wx_refund_id'] or wx_id, checked, refund_id))
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('refresh_refund', snapshot['order_no'], f'退款单 {refund_id}；微信状态 {status}', checked))
        if status in (5, 8):
            _flag_membership_review(db, refund_id, snapshot['order_no'])
        return _public_by_id(db, refund_id)


def review_refund(refund_id, data):
    if not re.fullmatch(r'R[a-f0-9]{30}', refund_id):
        raise HTTPException(400, '退款单号无效')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM refund_transactions WHERE refund_id=?', (refund_id,)).fetchone()
        if not row or row['state'] not in OPEN_STATES:
            raise HTTPException(409, '退款记录状态已变化，请刷新')
        if row['state'] == 'dispatching':
            created = datetime.fromisoformat(row['created_at'])
            if (datetime.now(timezone.utc) - created).total_seconds() < 90:
                raise HTTPException(409, '退款请求仍在发送，请稍后核对')
        if data.outcome == 'not_refunded' and (row['state'] == 'notice_success' or row['query_status'] in (5, 8)):
            raise HTTPException(409, '微信已返回退款相关状态，不能登记为未退款，请继续核对')
        detail = ('管理员核实退款完成：' if data.outcome == 'confirmed' else '管理员核实未退款：') + data.note
        db.execute('UPDATE refund_transactions SET state=?,detail=?,updated_at=? WHERE refund_id=?',
                   (data.outcome, detail, now_iso(), refund_id))
        if data.outcome == 'not_refunded':
            db.execute("UPDATE refund_entitlement_checks SET state='cancelled',detail=?,updated_at=? "
                       "WHERE order_no=? AND mch_refund_id=? AND state='pending'",
                       ('管理员核实未退款；如收到有效退款通知将重新核对', now_iso(), row['order_no'], refund_id))
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('review_refund', row['order_no'], f'退款单 {refund_id}；{detail}', now_iso()))
        if data.outcome == 'confirmed':
            _flag_membership_review(db, refund_id, row['order_no'])
        return _public_by_id(db, refund_id)
