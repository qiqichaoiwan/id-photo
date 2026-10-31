"""Membership catalog, entitlements and customer refund requests."""
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, validator

DATA_DIR = Path(os.environ.get('IDPHOTO_DATA_DIR', Path(__file__).resolve().parent / '.miniapp_data'))
DB_PATH = DATA_DIR / 'membership.sqlite3'


@contextmanager
def database():
    DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH), timeout=10)
    try:
        os.chmod(DB_PATH, 0o600)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with database() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS plans (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, months INTEGER NOT NULL, price_fen INTEGER NOT NULL,
          description TEXT NOT NULL DEFAULT '', wechat_product_id TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'draft', sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS members (
          subject TEXT PRIMARY KEY, expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
          order_no TEXT PRIMARY KEY, subject TEXT NOT NULL, plan_name TEXT NOT NULL,
          months INTEGER NOT NULL, price_fen INTEGER NOT NULL, status TEXT NOT NULL,
          created_at TEXT NOT NULL, expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS identity_users (
          user_id TEXT PRIMARY KEY, openid_hash TEXT NOT NULL UNIQUE,
          encrypted_openid BLOB NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS identity_aliases (
          subject TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES identity_users(user_id)
        );
        CREATE TABLE IF NOT EXISTS membership_grants (
          order_no TEXT PRIMARY KEY REFERENCES orders(order_no), subject TEXT NOT NULL,
          start_at TEXT NOT NULL, expires_at TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payment_events (
          event_key TEXT PRIMARY KEY, order_no TEXT, event_type TEXT NOT NULL,
          state TEXT NOT NULL, created_at TEXT NOT NULL, details TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS refund_requests (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_no TEXT NOT NULL REFERENCES orders(order_no),
          reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'submitted',
          response TEXT NOT NULL DEFAULT '', admin_note TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          CHECK (status IN ('submitted', 'processing', 'closed'))
        );
        CREATE TABLE IF NOT EXISTS refund_transactions (
          refund_id TEXT PRIMARY KEY, order_no TEXT NOT NULL REFERENCES orders(order_no),
          request_key TEXT NOT NULL UNIQUE, amount_fen INTEGER NOT NULL CHECK (amount_fen > 0),
          left_fee_before INTEGER NOT NULL CHECK (left_fee_before >= amount_fen),
          reason_code TEXT NOT NULL, note TEXT NOT NULL, pay_wx_order_id TEXT NOT NULL,
          state TEXT NOT NULL CHECK (state IN ('dispatching', 'accepted', 'unknown', 'notice_success', 'notice_failed', 'confirmed', 'not_refunded')),
          wx_refund_id TEXT NOT NULL DEFAULT '', platform_code INTEGER,
          detail TEXT NOT NULL DEFAULT '', query_status INTEGER, query_checked_at TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admin_audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, target TEXT NOT NULL,
          details TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS member_adjustments (
          id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL,
          previous_expires_at TEXT, new_expires_at TEXT NOT NULL,
          reason TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL
        );
        ''')
        columns = {row['name'] for row in db.execute('PRAGMA table_info(orders)').fetchall()}
        for column, declaration in (
            ('product_id', "TEXT NOT NULL DEFAULT ''"), ('platform_order_id', 'TEXT'),
            ('attach', "TEXT NOT NULL DEFAULT ''"), ('updated_at', "TEXT NOT NULL DEFAULT ''"),
            ('review_needed', 'INTEGER NOT NULL DEFAULT 0'), ('plan_id', 'INTEGER'),
            ('channel_order_id', 'TEXT'), ('notify_needed', 'INTEGER NOT NULL DEFAULT 0')
        ):
            if column not in columns:
                db.execute(f'ALTER TABLE orders ADD COLUMN {column} {declaration}')
        refund_columns = {row['name'] for row in db.execute('PRAGMA table_info(refund_transactions)').fetchall()}
        for column, declaration in (('query_status', 'INTEGER'), ('query_checked_at', "TEXT NOT NULL DEFAULT ''")):
            if column not in refund_columns:
                db.execute(f'ALTER TABLE refund_transactions ADD COLUMN {column} {declaration}')
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS orders_platform_id ON orders(platform_order_id) WHERE platform_order_id IS NOT NULL')
        db.execute('CREATE INDEX IF NOT EXISTS orders_pending ON orders(status, updated_at)')
        db.execute('CREATE INDEX IF NOT EXISTS orders_subject_created ON orders(subject, created_at)')
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS refund_requests_open_order ON refund_requests(order_no) WHERE status IN ('submitted', 'processing')")
        db.execute('CREATE INDEX IF NOT EXISTS refund_requests_created ON refund_requests(created_at)')
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS refund_transactions_one_open ON refund_transactions(order_no) WHERE state NOT IN ('confirmed', 'not_refunded')")
        db.execute('CREATE INDEX IF NOT EXISTS refund_transactions_order ON refund_transactions(order_no, created_at)')
        db.execute('CREATE INDEX IF NOT EXISTS adjustments_subject_created ON member_adjustments(subject, created_at)')
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM settings WHERE key = 'catalog_initialized'").fetchone():
            db.executemany('INSERT INTO plans (name, months, price_fen, description, sort_order) VALUES (?, ?, ?, ?, ?)', [
                ('1个月会员', 1, 1200, '会员免广告保存', 1),
                ('3个月会员', 3, 2400, '会员免广告保存', 2),
                ('12个月会员', 12, 6800, '会员免广告保存', 3),
            ])
            db.execute("INSERT INTO settings (key, value) VALUES ('catalog_initialized', '1')")


def subject_for(request: Request) -> str:
    subject = getattr(request.state, 'subject', None)
    if not subject:
        raise HTTPException(503, '会员服务需要启用微信登录')
    from miniapp_identity import resolve_subject
    return resolve_subject(subject)


USER_CTE = '''WITH subjects AS (SELECT user_id AS subject FROM identity_users
    UNION SELECT subject FROM members UNION SELECT subject FROM orders)'''


def resolve_user_ref(db, user_ref: str) -> str:
    """Resolve a public user reference only when it identifies exactly one subject."""
    if not re.fullmatch(r'[a-f0-9]{16}', user_ref):
        raise HTTPException(400, '用户编号无效')
    matches = db.execute(
        USER_CTE + ' SELECT subject FROM subjects WHERE substr(subject, 1, 16) = ? LIMIT 2',
        (user_ref,),
    ).fetchall()
    if len(matches) != 1:
        raise HTTPException(409 if matches else 404, '用户编号不唯一' if matches else '用户不存在')
    return matches[0]['subject']


def public_plan(row):
    result = {key: row[key] for key in ('id', 'name', 'months', 'price_fen', 'description', 'status')}
    from miniapp_payment import payment_enabled
    if not payment_enabled() and result['status'] == 'active':
        result['status'] = 'draft'
    return result


router = APIRouter(prefix='/membership')


@router.get('/profile')
def profile(request: Request, response: Response):
    """Return only the authenticated user's reference, without exposing their OpenID."""
    subject = subject_for(request)
    with database() as db:
        if not db.execute('SELECT 1 FROM identity_users WHERE user_id = ?', (subject,)).fetchone():
            # An older token may predate identity mapping; the client can log in again.
            raise HTTPException(401, '请重新登录后查看会员编号')
        user_ref = subject[:16]
        try:
            resolved = resolve_user_ref(db, user_ref)
        except HTTPException:
            raise HTTPException(503, '会员编号暂不可用，请稍后重试')
        if resolved != subject:
            raise HTTPException(503, '会员编号暂不可用，请稍后重试')
    response.headers['Cache-Control'] = 'private, no-store'
    return {'user_ref': user_ref}


@router.get('/plans')
def plans():
    with database() as db:
        rows = db.execute("SELECT * FROM plans WHERE status != 'archived' ORDER BY sort_order, id").fetchall()
        return [public_plan(row) for row in rows]


@router.get('/status')
def status(request: Request):
    subject = subject_for(request)
    with database() as db:
        row = db.execute('SELECT expires_at FROM members WHERE subject = ?', (subject,)).fetchone()
    if not row:
        return {'active': False, 'status': 'none', 'expires_at': None}
    try:
        expiration = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
        active = expiration.tzinfo is not None and expiration > datetime.now(timezone.utc)
    except (ValueError, TypeError):
        raise HTTPException(503, '会员状态暂不可用')
    return {'active': active, 'status': 'active' if active else 'expired', 'expires_at': row['expires_at']}


@router.get('/orders')
def orders(request: Request):
    subject = subject_for(request)
    with database() as db:
        return [dict(row) for row in db.execute('SELECT order_no, plan_name, months, price_fen, status, created_at, expires_at, review_needed FROM orders WHERE subject = ? ORDER BY created_at DESC LIMIT 100', (subject,)).fetchall()]


@router.get('/orders/{order_no}')
def order(order_no: str, request: Request):
    subject = subject_for(request)
    with database() as db:
        row = db.execute('SELECT order_no, plan_name, months, price_fen, status, created_at, expires_at, review_needed FROM orders WHERE subject = ? AND order_no = ?', (subject, order_no)).fetchone()
        if not row:
            raise HTTPException(404, '订单不存在')
        result = dict(row)
        refund = db.execute('''SELECT status, response, created_at, updated_at FROM refund_requests
                               WHERE order_no = ? ORDER BY id DESC LIMIT 1''', (order_no,)).fetchone()
        result['refund_request'] = dict(refund) if refund else None
        return result


class RefundRequestInput(BaseModel):
    reason: str = Field(min_length=2, max_length=200)

    @validator('reason')
    def reason_not_blank(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError('请填写退款原因')
        return value


@router.post('/orders/{order_no}/refund-requests')
def request_refund(order_no: str, data: RefundRequestInput, request: Request):
    """Record a request for human review; never initiate a payment or change membership."""
    subject = subject_for(request)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT status FROM orders WHERE order_no = ? AND subject = ?',
                         (order_no, subject)).fetchone()
        if not row:
            raise HTTPException(404, '订单不存在')
        if row['status'] != 'paid':
            raise HTTPException(409, '订单支付完成后才能申请退款')
        existing = db.execute('''SELECT status, response, created_at, updated_at FROM refund_requests
                                 WHERE order_no = ? AND status IN ('submitted', 'processing')
                                 ORDER BY id DESC LIMIT 1''', (order_no,)).fetchone()
        if existing:
            return dict(existing)
        refunded = db.execute('''SELECT 1 FROM payment_events WHERE order_no = ?
                                 AND event_type = 'xpay_refund_notify'
                                 AND state IN ('manual_review', 'resolved') LIMIT 1''', (order_no,)).fetchone()
        if refunded:
            raise HTTPException(409, '该订单的退款记录正在核对，请查看退款进度或联系商家')
        now = datetime.now(timezone.utc).isoformat()
        db.execute('''INSERT INTO refund_requests(order_no, reason, created_at, updated_at)
                      VALUES (?, ?, ?, ?)''', (order_no, data.reason, now, now))
        return {'status': 'submitted', 'response': '', 'created_at': now, 'updated_at': now}
