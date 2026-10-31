"""Verify completed refunds before removing their membership entitlement."""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import requests
from fastapi import HTTPException

from miniapp_membership import database

LOG = logging.getLogger('idphoto.refund_entitlements')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('missing timezone')
    return result.astimezone(timezone.utc)


def _check_key(order_no, mch_refund_id, wx_refund_id):
    identity = 'm:' + mch_refund_id if mch_refund_id else 'w:' + wx_refund_id
    return hashlib.sha256((order_no + ':' + identity).encode()).hexdigest()


def _flag_review(db, order_no, key, detail):
    event_key = hashlib.sha256(('refund-entitlement:' + key).encode()).hexdigest()
    db.execute('''INSERT OR IGNORE INTO payment_events(event_key,order_no,event_type,state,created_at,details)
                  VALUES (?,?,'order_verification','manual_review',?,?)''',
               (event_key, order_no, _now(), detail[:300]))
    event = db.execute('SELECT state FROM payment_events WHERE event_key=?', (event_key,)).fetchone()
    if event and event['state'] == 'manual_review':
        db.execute('UPDATE orders SET review_needed=1,updated_at=? WHERE order_no=?', (_now(), order_no))


def enqueue_check(db, order_no, mch_refund_id, wx_refund_id, amount_fen,
                  payment_wx_order_id='', source='admin'):
    """Add a check inside the caller's transaction; never alter membership here."""
    if (not isinstance(order_no, str) or not order_no or len(order_no) > 128
            or not isinstance(mch_refund_id, str) or len(mch_refund_id) > 128
            or not isinstance(wx_refund_id, str) or len(wx_refund_id) > 128
            or not (mch_refund_id or wx_refund_id)
            or not isinstance(payment_wx_order_id, str) or len(payment_wx_order_id) > 128
            or type(amount_fen) is not int or amount_fen <= 0):
        return None
    key = _check_key(order_no, mch_refund_id, wx_refund_id)
    existing = db.execute('SELECT * FROM refund_entitlement_checks WHERE check_key=?', (key,)).fetchone()
    if existing:
        conflict = (existing['order_no'] != order_no or existing['amount_fen'] != amount_fen
                    or (existing['wx_refund_id'] and wx_refund_id
                        and not hmac.compare_digest(existing['wx_refund_id'], wx_refund_id))
                    or (existing['payment_wx_order_id'] and payment_wx_order_id
                        and not hmac.compare_digest(existing['payment_wx_order_id'], payment_wx_order_id)))
        if conflict:
            db.execute("UPDATE refund_entitlement_checks SET state='manual_review',detail=?,updated_at=? WHERE check_key=? AND state!='revoked'",
                       ('退款通知与已有记录不一致，请人工核对', _now(), key))
            _flag_review(db, order_no, key, '退款通知与已有记录不一致，请人工核对')
            return None
        db.execute('''UPDATE refund_entitlement_checks SET wx_refund_id=?,payment_wx_order_id=?,
                      state=CASE WHEN state='cancelled' AND ?='notice' THEN 'pending' ELSE state END,
                      updated_at=? WHERE check_key=?''',
                   (existing['wx_refund_id'] or wx_refund_id,
                    existing['payment_wx_order_id'] or payment_wx_order_id, source, _now(), key))
        return key
    now = _now()
    db.execute('''INSERT INTO refund_entitlement_checks(check_key,order_no,mch_refund_id,wx_refund_id,
        payment_wx_order_id,amount_fen,source,state,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,'pending',?,?)''',
        (key, order_no, mch_refund_id, wx_refund_id, payment_wx_order_id, amount_fen, source, now, now))
    return key


def enqueue_notice(event, order_no):
    """Queue a signed, decrypted notification only after matching its buyer."""
    from miniapp_identity import get_openid
    from miniapp_payment import payment_env

    amount, code = event.get('RefundFee'), event.get('RetCode')
    mch, wx = event.get('MchRefundId', ''), event.get('WxRefundId', '')
    payment_id, mch_order = event.get('WxOrderId', ''), event.get('MchOrderId', '')
    if (not order_no or type(code) is not int or code != 0 or str(event.get('Env')) != str(payment_env())
            or type(amount) is not int or amount <= 0 or not isinstance(mch, str) or not isinstance(wx, str)
            or not (mch or wx) or not isinstance(payment_id, str) or not isinstance(mch_order, str)):
        return None
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        order = db.execute('SELECT * FROM orders WHERE order_no=?', (order_no,)).fetchone()
        if (not order or amount > order['price_fen'] or not isinstance(event.get('OpenId'), str)
                or not hmac.compare_digest(event['OpenId'], get_openid(order['subject']))):
            return None
        if not mch_order or mch_order not in (order['order_no'], order['channel_order_id'] or ''):
            return None
        if order['platform_order_id'] and payment_id and not hmac.compare_digest(order['platform_order_id'], payment_id):
            return None
        transaction = db.execute('SELECT * FROM refund_transactions WHERE refund_id=?', (mch,)).fetchone() if mch else None
        if transaction and (transaction['order_no'] != order_no or transaction['amount_fen'] != amount
                            or (transaction['wx_refund_id'] and wx
                                and not hmac.compare_digest(transaction['wx_refund_id'], wx))
                            or (payment_id and not hmac.compare_digest(transaction['pay_wx_order_id'], payment_id))):
            return None
        return enqueue_check(db, order_no, mch, wx, amount, payment_id, 'notice')


def _query_refund(check, subject):
    from miniapp_identity import get_openid
    from miniapp_payment import pay_sig, payment_env, wechat_access_token

    body_data = {'openid': get_openid(subject), 'env': payment_env()}
    if check['wx_refund_id']:
        body_data['wx_order_id'] = check['wx_refund_id']
    else:
        body_data['order_id'] = check['mch_refund_id']
    body = json.dumps(body_data, separators=(',', ':'))
    response = requests.post('https://api.weixin.qq.com/xpay/query_order',
        params={'access_token': wechat_access_token(), 'pay_sig': pay_sig('/xpay/query_order', body)},
        data=body.encode(), headers={'Content-Type': 'application/json'}, timeout=8)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get('errcode') != 0 or not isinstance(data.get('order'), dict):
        raise HTTPException(503, '微信退款单暂不可查询')
    return data['order']


def _replay(grants, adjustments, revocations):
    """Rebuild grant periods, preserving time consumed before each refund."""
    from miniapp_payment import plus_calendar_months

    entries = [(_time(g['created_at']), 'grant', g) for g in grants]
    entries += [(_time(a['created_at']), 'adjustment', a) for a in adjustments if a['source'] != 'refund_auto']
    entries += [(_time(r['created_at']), 'revocation', r) for r in revocations]
    entries.sort(key=lambda item: item[0])
    if any(entries[i - 1][0] == entries[i][0] for i in range(1, len(entries))):
        raise ValueError('ambiguous membership history')
    expiry = None
    baseline = None
    periods = []
    for when, kind, item in entries:
        if kind == 'adjustment':
            expiry = _time(item['new_expires_at'])
            baseline, periods = expiry, []
        elif kind == 'grant':
            start = max(when, expiry) if expiry else when
            expiry = plus_calendar_months(start, item['months'])
            periods.append({'order_no': item['order_no'], 'created_at': when, 'months': item['months'],
                            'start': start, 'end': expiry})
        else:
            index = next((i for i, p in enumerate(periods) if p['order_no'] == item['order_no']), None)
            if index is None:
                raise ValueError('退款订单的发放历史缺失')
            target = periods[index]
            if target['end'] <= when:
                continue  # The order's time was already consumed; keep other orders intact.
            if target['start'] < when:
                target['end'] = when
                cursor, start_index = when, index + 1
            else:
                periods.pop(index)
                cursor = periods[index - 1]['end'] if index else baseline
                start_index = index
            for later in periods[start_index:]:
                later['start'] = max(when, later['created_at'], cursor) if cursor else max(when, later['created_at'])
                later['end'] = plus_calendar_months(later['start'], later['months'])
                cursor = later['end']
            expiry = cursor
    return expiry


def _revoke(db, check, order):
    previous_revocation = db.execute('SELECT 1 FROM membership_refund_revocations WHERE order_no=?', (order['order_no'],)).fetchone()
    if previous_revocation:
        return 'revoked', '该订单权益已回收'
    member = db.execute('SELECT expires_at FROM members WHERE subject=?', (order['subject'],)).fetchone()
    grants = db.execute('''SELECT g.order_no,g.created_at,g.start_at,g.expires_at,o.months FROM membership_grants g
        JOIN orders o ON o.order_no=g.order_no WHERE g.subject=?''', (order['subject'],)).fetchall()
    adjustments = db.execute('SELECT * FROM member_adjustments WHERE subject=?', (order['subject'],)).fetchall()
    target = next((g for g in grants if g['order_no'] == order['order_no']), None)
    if not member or not target:
        raise ValueError('缺少会员或订单发放记录')
    target_time = _time(target['created_at'])
    if any(a['source'] != 'refund_auto' and _time(a['created_at']) >= target_time for a in adjustments):
        raise ValueError('订单发放后存在人工会员调整')
    revocations = [dict(r) for r in db.execute('SELECT order_no,created_at FROM membership_refund_revocations WHERE subject=?', (order['subject'],))]
    actual = _time(member['expires_at'])
    reconstructed = _replay(grants, adjustments, revocations)
    if reconstructed != actual:
        raise ValueError('会员历史与当前到期时间不一致')
    now = datetime.now(timezone.utc)
    recalculated = _replay(grants, adjustments, revocations + [{'order_no': order['order_no'], 'created_at': now.isoformat()}])
    new_expiry = recalculated if recalculated is not None else min(actual, now)
    if new_expiry > actual:
        raise ValueError('回收后的到期时间异常')
    now_text, new_text = now.isoformat(), new_expiry.isoformat()
    db.execute('UPDATE members SET expires_at=? WHERE subject=?', (new_text, order['subject']))
    db.execute('''INSERT INTO membership_refund_revocations(order_no,subject,check_key,previous_expires_at,new_expires_at,created_at)
        VALUES (?,?,?,?,?,?)''', (order['order_no'], order['subject'], check['check_key'], member['expires_at'], new_text, now_text))
    db.execute('''INSERT INTO member_adjustments(subject,previous_expires_at,new_expires_at,reason,source,created_at)
        VALUES (?,?,?,?, 'refund_auto',?)''', (order['subject'], member['expires_at'], new_text, '全额退款后回收该订单会员权益', now_text))
    db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
               ('refund_auto_revoke', order['order_no'], f"全额退款自动回收；{member['expires_at']} → {new_text}", now_text))
    return 'revoked', '已自动回收该订单对应的会员权益'


def process_check(key):
    """Verify both WeChat orders, then atomically remove at most one grant."""
    from miniapp_payment import payment_env
    from miniapp_refund import _query_payment_order

    with database() as db:
        row = db.execute('SELECT * FROM refund_entitlement_checks WHERE check_key=?', (key,)).fetchone()
        if not row or row['state'] != 'pending':
            return
        check = dict(row)
        order_row = db.execute('SELECT * FROM orders WHERE order_no=?', (check['order_no'],)).fetchone()
        if not order_row:
            return
        order = dict(order_row)
    try:
        refund = _query_refund(check, order['subject'])
        original = _query_payment_order(order)
    except HTTPException as exc:
        if exc.status_code == 409:
            detail = '微信原订单标识、渠道或环境不匹配，请人工核对会员'
            with database() as db:
                db.execute('BEGIN IMMEDIATE')
                updated = db.execute("""UPDATE refund_entitlement_checks SET state='manual_review',detail=?,updated_at=?
                    WHERE check_key=? AND state='pending' AND order_no=? AND mch_refund_id=?
                    AND wx_refund_id=? AND payment_wx_order_id=? AND amount_fen=?""",
                    (detail, _now(), key, check['order_no'], check['mch_refund_id'], check['wx_refund_id'],
                     check['payment_wx_order_id'], check['amount_fen']))
                if updated.rowcount:
                    _flag_review(db, check['order_no'], key, detail)
            return
        with database() as db:
            db.execute("UPDATE refund_entitlement_checks SET detail=?,updated_at=? WHERE check_key=? AND state='pending'",
                       ('微信退款单暂不可确认，将自动重试', _now(), key))
        return
    except (requests.RequestException, ValueError, TypeError):
        with database() as db:
            db.execute("UPDATE refund_entitlement_checks SET detail=?,updated_at=? WHERE check_key=? AND state='pending'",
                       ('微信退款单暂不可确认，将自动重试', _now(), key))
        return
    status = refund.get('status')
    wx_id = refund.get('wx_order_id')
    original_wx = original.get('wx_order_id')
    valid = (type(refund.get('order_type')) is int and refund['order_type'] in (1, 8)
             and refund['order_type'] == (8 if original['order_type'] == 7 else 1)
             and refund.get('env_type') == payment_env() + 1
             and type(refund.get('refund_fee')) is int and refund['refund_fee'] == check['amount_fen']
             and (not check['mch_refund_id'] or refund.get('order_id') == check['mch_refund_id'])
             and isinstance(wx_id, str) and 0 < len(wx_id) <= 128
             and (not check['wx_refund_id'] or hmac.compare_digest(wx_id, check['wx_refund_id']))
             and isinstance(original_wx, str) and 0 < len(original_wx) <= 128
             and (not order['platform_order_id'] or hmac.compare_digest(original_wx, order['platform_order_id']))
             and (not check['payment_wx_order_id'] or hmac.compare_digest(original_wx, check['payment_wx_order_id']))
             and type(original.get('order_fee')) is int and original['order_fee'] == order['price_fen']
             and type(original.get('paid_fee')) is int and original['paid_fee'] == order['price_fen']
             and type(original.get('left_fee')) is int and 0 <= original['left_fee'] <= order['price_fen']
             and type(status) is int)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        current = db.execute('SELECT * FROM refund_entitlement_checks WHERE check_key=?', (key,)).fetchone()
        current_order = db.execute('SELECT * FROM orders WHERE order_no=?', (check['order_no'],)).fetchone()
        if not current or current['state'] != 'pending' or not current_order:
            return
        if (any(current_order[k] != order[k] for k in ('subject', 'price_fen', 'product_id', 'platform_order_id'))
                or any(current[k] != check[k] for k in ('order_no', 'mch_refund_id', 'wx_refund_id', 'payment_wx_order_id', 'amount_fen'))):
            return  # A concurrent notification updated the evidence; retry with the new snapshot.
        if not valid:
            state, detail = 'manual_review', '退款单或支付单信息不匹配，请人工核对会员'
        elif status == 7:
            state, detail = 'manual_review', '微信退款单显示失败，请人工核对'
        elif status != 8:
            state, detail = 'pending', '退款尚未确认完成，将自动重试'
        elif original['left_fee'] > 0:
            state, detail = 'partial', '订单为部分退款，会员权益请人工核对'
        elif original.get('status') not in (5, 8):
            state, detail = 'pending', '等待微信原订单退款状态同步'
        else:
            try:
                state, detail = _revoke(db, current, current_order)
            except (ValueError, TypeError, OverflowError, KeyError) as exc:
                state, detail = 'manual_review', f'无法安全计算会员权益：{exc}'
        db.execute('UPDATE refund_entitlement_checks SET state=?,detail=?,updated_at=? WHERE check_key=?',
                   (state, detail, _now(), key))
        if state in ('partial', 'manual_review'):
            _flag_review(db, check['order_no'], key, detail)


def process_pending_checks(limit=20):
    with database() as db:
        keys = [row['check_key'] for row in db.execute("SELECT check_key FROM refund_entitlement_checks WHERE state='pending' ORDER BY updated_at LIMIT ?", (limit,)).fetchall()]
    for key in keys:
        try:
            process_check(key)
        except Exception:
            LOG.warning('退款会员权益核对暂不可用')
            with database() as db:
                db.execute("UPDATE refund_entitlement_checks SET updated_at=? WHERE check_key=? AND state='pending'", (_now(), key))
