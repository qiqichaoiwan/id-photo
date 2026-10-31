"""Operations console for the mini-program, with an optional protected hostname."""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import socket
import threading
import time
from collections import OrderedDict, deque
from pathlib import Path
from typing import Literal, Optional
from datetime import date, datetime, timedelta, timezone

import requests
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from miniapp_membership import DATA_DIR, USER_CTE, database, initialize, resolve_user_ref
from miniapp_telemetry import read_metrics

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
security = HTTPBasic()
PASSWORD_FILE = DATA_DIR / 'admin.json'
ADMIN_PORT = int(os.environ.get('IDPHOTO_ADMIN_PORT', '8091'))
ADMIN_PUBLIC_HOST = os.environ.get('IDPHOTO_ADMIN_PUBLIC_HOST', '').strip().lower()
if ADMIN_PUBLIC_HOST and not re.fullmatch(r'[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?)+', ADMIN_PUBLIC_HOST):
    raise RuntimeError('IDPHOTO_ADMIN_PUBLIC_HOST 必须是有效的主机名')
ATTEMPTS = OrderedDict()
ATTEMPTS_LOCK = threading.Lock()


class LocalOnly(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        host = request.headers.get('host', '').lower()
        if not request.client or request.client.host not in ('127.0.0.1', '::1'):
            return PlainTextResponse('Forbidden', status_code=403)
        public = bool(ADMIN_PUBLIC_HOST) and host == ADMIN_PUBLIC_HOST
        if public:
            # Cloudflared must validate the Access JWT before forwarding here.
            # Its listener is loopback-only; forwarded headers are never trusted
            # from direct network clients.
            if request.headers.get('x-forwarded-proto', '').lower() != 'https' or not request.headers.get('cf-access-jwt-assertion'):
                return PlainTextResponse('Forbidden', status_code=403)
            try:
                client = str(ipaddress.ip_address(request.headers.get('cf-connecting-ip', '')))
            except ValueError:
                return PlainTextResponse('Forbidden', status_code=403)
            expected_origin = 'https://' + ADMIN_PUBLIC_HOST
        elif host in (f'127.0.0.1:{ADMIN_PORT}', f'localhost:{ADMIN_PORT}'):
            client = 'local'
            expected_origin = 'http://' + host
        else:
            return PlainTextResponse('Forbidden', status_code=403)
        origin = request.headers.get('origin')
        if origin and origin != expected_origin:
            return PlainTextResponse('Forbidden', status_code=403)
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and (origin != expected_origin or request.headers.get('x-admin-request') != '1'):
            return PlainTextResponse('Forbidden', status_code=403)
        request.state.admin_client = client
        response = await call_next(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
        if public:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response


app.add_middleware(LocalOnly)


def require_admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    now = time.monotonic()
    client = request.state.admin_client
    with ATTEMPTS_LOCK:
        attempts = ATTEMPTS.get(client, deque())
        while attempts and now - attempts[0] >= 300:
            attempts.popleft()
        if len(attempts) >= 8:
            raise HTTPException(429, '尝试次数过多，请稍后再试')
    try:
        info = json.loads(PASSWORD_FILE.read_text())
        salt = base64.b64decode(info['salt'], validate=True)
        expected = base64.b64decode(info['hash'], validate=True)
        actual = hashlib.scrypt(credentials.password.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)
        good = hmac.compare_digest(credentials.username.encode('utf-8'), b'admin') and hmac.compare_digest(actual, expected)
    except (OSError, ValueError, KeyError, TypeError):
        good = False
    if not good:
        with ATTEMPTS_LOCK:
            if client not in ATTEMPTS and len(ATTEMPTS) >= 4096:
                ATTEMPTS.popitem(last=False)
            ATTEMPTS.setdefault(client, deque()).append(now)
            ATTEMPTS.move_to_end(client)
        raise HTTPException(401, '管理员账号或密码错误', headers={'WWW-Authenticate': 'Basic realm="Membership Admin"'})


class PlanInput(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    months: int = Field(ge=1, le=120)
    price_fen: int = Field(ge=1, le=10000000)
    description: str = Field(default='', max_length=100)
    wechat_product_id: str = Field(default='', max_length=64)
    sort_order: int = Field(default=0, ge=0, le=10000)
    status: str = 'draft'

    @validator('name')
    def trim_name(cls, value):
        if not value.strip():
            raise ValueError('请输入套餐名称')
        return value.strip()

    @validator('wechat_product_id')
    def product_id_format(cls, value):
        if value and not re.fullmatch(r'[A-Za-z0-9_-]+', value):
            raise ValueError('商品 ID 格式无效')
        return value

    @validator('status')
    def allowed_status(cls, value):
        if value not in ('draft', 'archived'):
            raise ValueError('支付未完成，套餐只能设为草稿或归档')
        return value


@app.on_event('startup')
def startup():
    if not PASSWORD_FILE.is_file():
        raise RuntimeError('请先运行 setup_membership_admin.py 设置管理员密码')
    initialize()


@app.get('/', response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def index():
    return (Path(__file__).resolve().parent / 'miniapp_admin.html').read_text(encoding='utf-8')


@app.get('/admin.css', dependencies=[Depends(require_admin)])
def admin_css():
    return FileResponse(Path(__file__).resolve().parent / 'miniapp_admin.css', media_type='text/css')


@app.get('/admin.js', dependencies=[Depends(require_admin)])
def admin_js():
    return FileResponse(Path(__file__).resolve().parent / 'miniapp_admin.js', media_type='application/javascript')


@app.get('/api/plans', dependencies=[Depends(require_admin)])
def list_plans():
    with database() as db:
        return [dict(row) for row in db.execute('SELECT * FROM plans ORDER BY sort_order, id').fetchall()]


@app.post('/api/plans', dependencies=[Depends(require_admin)])
def add_plan(plan: PlanInput):
    with database() as db:
        result = db.execute('INSERT INTO plans (name, months, price_fen, description, wechat_product_id, sort_order, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            (plan.name, plan.months, plan.price_fen, plan.description, plan.wechat_product_id, plan.sort_order, plan.status))
        db.execute('INSERT INTO admin_audit (action, target, details, created_at) VALUES (?, ?, ?, ?)', ('create_plan', str(result.lastrowid), '创建套餐草稿', datetime.now(timezone.utc).isoformat()))
        return {'id': result.lastrowid}


@app.put('/api/plans/{plan_id}', dependencies=[Depends(require_admin)])
def update_plan(plan_id: int, plan: PlanInput):
    with database() as db:
        result = db.execute('UPDATE plans SET name=?, months=?, price_fen=?, description=?, wechat_product_id=?, sort_order=?, status=? WHERE id=?',
                            (plan.name, plan.months, plan.price_fen, plan.description, plan.wechat_product_id, plan.sort_order, plan.status, plan_id))
        if result.rowcount == 0:
            raise HTTPException(404, '套餐不存在')
        db.execute('INSERT INTO admin_audit (action, target, details, created_at) VALUES (?, ?, ?, ?)', ('edit_plan', str(plan_id), '修改套餐并设为草稿或归档', datetime.now(timezone.utc).isoformat()))
        return {'id': plan_id}


class ActivationInput(BaseModel):
    product_id: str = Field(min_length=1, max_length=64)
    price_fen: int = Field(ge=1)
    published: bool


@app.post('/api/plans/{plan_id}/activate', dependencies=[Depends(require_admin)])
def activate_plan(plan_id: int, data: ActivationInput):
    if not data.published:
        raise HTTPException(400, '请先核对微信商品已发布')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        plan = db.execute('SELECT * FROM plans WHERE id = ?', (plan_id,)).fetchone()
        if not plan:
            raise HTTPException(404, '套餐不存在')
        if not plan['wechat_product_id'] or data.product_id != plan['wechat_product_id'] or data.price_fen != plan['price_fen']:
            raise HTTPException(409, '商品 ID 或价格与套餐不一致')
        if plan['status'] == 'archived':
            raise HTTPException(409, '请先将套餐恢复为草稿')
        duplicate = db.execute("SELECT id FROM plans WHERE id != ? AND status = 'active' AND wechat_product_id = ? LIMIT 1",
                               (plan_id, plan['wechat_product_id'])).fetchone()
        if duplicate:
            raise HTTPException(409, '该微信商品已关联其他上架套餐')
        db.execute("UPDATE plans SET status = 'active' WHERE id = ?", (plan_id,))
        db.execute('INSERT INTO admin_audit (action, target, details, created_at) VALUES (?, ?, ?, ?)',
                   ('activate_plan', str(plan_id), '管理员确认商品已发布并核对价格', datetime.now(timezone.utc).isoformat()))
        return {'id': plan_id}


@app.get('/api/orders', dependencies=[Depends(require_admin)])
def list_orders(page: int = Query(1, ge=1, le=10000),
                page_size: int = Query(20, ge=1, le=100),
                order_no: str = Query('', max_length=128),
                status: Literal['all', 'pending', 'paid', 'closed'] = 'all',
                review: bool = False, date_from: str = '', date_to: str = ''):
    clauses, args = [], []
    if order_no.strip():
        clauses.append('instr(order_no, ?) > 0')
        args.append(order_no.strip())
    if status != 'all':
        clauses.append('status = ?')
        args.append(status)
    if review:
        clauses.append('review_needed = 1')
    bounds = []
    for value in (date_from, date_to):
        try:
            bounds.append(date.fromisoformat(value) if value else None)
        except ValueError:
            raise HTTPException(400, '日期格式无效')
    if bounds[0] and bounds[1] and bounds[0] > bounds[1]:
        raise HTTPException(400, '开始日期不能晚于结束日期')
    china = timezone(timedelta(hours=8))
    if bounds[0]:
        clauses.append('julianday(created_at) >= julianday(?)')
        args.append(datetime.combine(bounds[0], datetime.min.time(), china).isoformat())
    if bounds[1]:
        if bounds[1] == date.max:
            raise HTTPException(400, '结束日期超出范围')
        clauses.append('julianday(created_at) < julianday(?)')
        args.append(datetime.combine(bounds[1] + timedelta(days=1), datetime.min.time(), china).isoformat())
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    with database() as db:
        total = db.execute('SELECT COUNT(*) FROM orders' + where, args).fetchone()[0]
        orders = [dict(row) for row in db.execute('''SELECT order_no, substr(subject, 1, 16) AS user_ref,
            plan_name, months, price_fen, status, created_at, expires_at, product_id,
            platform_order_id, channel_order_id, review_needed, notify_needed FROM orders''' + where +
            ' ORDER BY created_at DESC, order_no DESC LIMIT ? OFFSET ?', args + [page_size, (page - 1) * page_size]).fetchall()]
        events = [dict(row) for row in db.execute("SELECT event_key, order_no, event_type, state, created_at, details FROM payment_events WHERE state IN ('manual_review', 'refund_failed', 'unhandled') ORDER BY created_at DESC LIMIT 100").fetchall()]
        return {'orders': orders, 'events': events, 'total': total, 'page': page, 'page_size': page_size}


@app.get('/api/overview', dependencies=[Depends(require_admin)])
def overview():
    with database() as db:
        users = db.execute('''SELECT COUNT(*) FROM (SELECT user_id AS subject FROM identity_users
            UNION SELECT subject FROM members UNION SELECT subject FROM orders)''').fetchone()[0]
        active = db.execute("SELECT COUNT(*) FROM members WHERE julianday(expires_at) > julianday('now')").fetchone()[0]
        order_counts = {row['status']: row['count'] for row in
                        db.execute('SELECT status, COUNT(*) AS count FROM orders GROUP BY status')}
        reviews = db.execute("SELECT COUNT(*) FROM payment_events WHERE state IN ('manual_review', 'refund_failed', 'unhandled')").fetchone()[0]
        refund_requests = db.execute("SELECT COUNT(*) FROM refund_requests WHERE status IN ('submitted', 'processing')").fetchone()[0]
        flagged_orders = db.execute('SELECT COUNT(*) FROM orders WHERE review_needed = 1').fetchone()[0]
    return {'users': users, 'active_members': active, 'orders': sum(order_counts.values()),
            'paid_orders': order_counts.get('paid', 0), 'pending_orders': order_counts.get('pending', 0),
            'review_events': reviews, 'review_orders': flagged_orders, 'refund_requests': refund_requests}


def probe_service(url, failure_note):
    """Probe a fixed endpoint, without following redirects or proxy settings."""
    try:
        session = requests.Session()
        session.trust_env = False
        with session.get(url, timeout=(1, 2),
                         allow_redirects=False, stream=True) as response:
            response.raise_for_status()
            payload = b''
            for chunk in response.iter_content(8192):
                payload += chunk
                if len(payload) > 65536:
                    raise ValueError('status response too large')
        result = json.loads(payload)
        if (not isinstance(result, dict) or result.get('status') not in ('ok', 'degraded')
                or not isinstance(result.get('checks'), list)):
            raise ValueError('invalid status response')
        checks = []
        for item in result['checks'][:30]:
            if isinstance(item, dict) and item.get('state') in ('ok', 'degraded', 'unavailable', 'unknown', 'disabled'):
                checks.append({key: str(item.get(key, ''))[:200] for key in ('id', 'name', 'state', 'detail')})
        return {'reachable': True, 'status': result['status'], 'checked_at': str(result.get('checked_at', ''))[:40],
                'checks': checks, 'note': str(result.get('note', ''))[:300]}
    except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
        return {'reachable': False, 'status': 'unavailable', 'checked_at': datetime.now(timezone.utc).isoformat(),
                'checks': [], 'note': failure_note}


def fetch_service_status():
    """Probe the running API and public tunnel, never this process's memory."""
    local = probe_service('http://127.0.0.1:8080/service-status', '本机照片服务未响应；无法判断是服务故障还是连接问题。')
    public = probe_service('https://photo.ruize.eu.org/service-status', '本机无法通过公网连接，可能与本机网络、隧道或服务有关。')
    local['public'] = {key: public[key] for key in ('reachable', 'status', 'checked_at', 'note')}
    try:
        with socket.create_connection(('127.0.0.1', 8092), timeout=0.5):
            push = {'id': 'push', 'name': '支付消息推送', 'state': 'ok', 'detail': '本机接收端口正在监听；未验证微信消息能否送达。'}
    except OSError:
        push = {'id': 'push', 'name': '支付消息推送', 'state': 'unavailable', 'detail': '本机接收端口未响应；微信订单消息可能无法送达。'}
    local['checks'].append(push)
    if local['reachable'] and (not public['reachable'] or public['status'] != 'ok' or push['state'] != 'ok'):
        local['status'] = 'degraded'
    return local


@app.get('/api/service', dependencies=[Depends(require_admin)])
def service():
    return fetch_service_status()


@app.get('/api/metrics', dependencies=[Depends(require_admin)])
def metrics(days: int = Query(7, ge=1, le=30)):
    return read_metrics(days)


def resolve_user(db, user_ref):
    return resolve_user_ref(db, user_ref)


@app.get('/api/users', dependencies=[Depends(require_admin)])
def list_users(page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=100),
               search: str = Query('', max_length=16),
               status: Literal['all', 'active', 'expired', 'none', 'unknown'] = 'all'):
    search = search.strip().lower()
    if search and not re.fullmatch(r'[a-f0-9]{1,16}', search):
        raise HTTPException(400, '请输入用户编号中的十六进制字符')
    clauses, args = [], []
    if search:
        clauses.append('substr(s.subject, 1, ?) = ?')
        args.extend([len(search), search])
    status_sql = "CASE WHEN m.expires_at IS NULL THEN 'none' WHEN julianday(m.expires_at) IS NULL THEN 'unknown' WHEN julianday(m.expires_at) > julianday('now') THEN 'active' ELSE 'expired' END"
    if status != 'all':
        clauses.append(status_sql + ' = ?')
        args.append(status)
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    join = ' FROM subjects s LEFT JOIN identity_users u ON u.user_id=s.subject LEFT JOIN members m ON m.subject=s.subject'
    with database() as db:
        total = db.execute(USER_CTE + ' SELECT COUNT(*)' + join + where, args).fetchone()[0]
        rows = db.execute(USER_CTE + ''' SELECT substr(s.subject,1,16) AS user_ref,
            u.created_at, m.expires_at, ''' + status_sql + ''' AS member_status,
            (SELECT COUNT(*) FROM orders o WHERE o.subject=s.subject) AS order_count,
            (SELECT COUNT(*) FROM orders o WHERE o.subject=s.subject AND o.review_needed=1) AS review_count''' +
            join + where + ' ORDER BY COALESCE(u.created_at, m.expires_at, \'\') DESC, s.subject LIMIT ? OFFSET ?',
            args + [page_size, (page - 1) * page_size]).fetchall()
    return {'users': [dict(row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


@app.get('/api/users/{user_ref}', dependencies=[Depends(require_admin)])
def user_detail(user_ref: str):
    with database() as db:
        subject = resolve_user(db, user_ref)
        user = db.execute('SELECT created_at FROM identity_users WHERE user_id=?', (subject,)).fetchone()
        member = db.execute('SELECT expires_at FROM members WHERE subject=?', (subject,)).fetchone()
        orders = db.execute('''SELECT order_no, plan_name, months, price_fen, status, created_at, review_needed
            FROM orders WHERE subject=? ORDER BY created_at DESC LIMIT 100''', (subject,)).fetchall()
        grants = db.execute('''SELECT g.order_no, g.start_at, g.expires_at, g.created_at FROM membership_grants g
            JOIN orders o ON o.order_no=g.order_no WHERE o.subject=? ORDER BY g.created_at DESC LIMIT 100''', (subject,)).fetchall()
        adjustments = db.execute('''SELECT previous_expires_at, new_expires_at, reason, source, created_at
            FROM member_adjustments WHERE subject=? ORDER BY id DESC LIMIT 100''', (subject,)).fetchall()
    return {'user_ref': user_ref, 'created_at': user['created_at'] if user else None,
            'expires_at': member['expires_at'] if member else None, 'orders': [dict(row) for row in orders],
            'grants': [dict(row) for row in grants], 'adjustments': [dict(row) for row in adjustments]}


class MemberAdjustmentInput(BaseModel):
    mode: Literal['extend', 'set']
    months: Optional[int] = Field(default=None, ge=1, le=120)
    new_expires_at: Optional[str] = Field(default=None, max_length=40)
    expected_expires_at: Optional[str] = Field(default=None, max_length=40)
    reason: str = Field(min_length=2, max_length=200)


def parse_expiry(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('timezone required')
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        raise HTTPException(400, '到期时间需要包含时区，例如 2027-01-01T12:00:00+08:00')


@app.post('/api/users/{user_ref}/adjust', dependencies=[Depends(require_admin)])
def adjust_member(user_ref: str, data: MemberAdjustmentInput):
    reason = data.reason.strip()
    if len(reason) < 2:
        raise HTTPException(400, '请填写调整原因')
    if data.mode == 'extend' and data.months is None:
        raise HTTPException(400, '请填写延长月数')
    if data.mode == 'set' and not data.new_expires_at:
        raise HTTPException(400, '请填写到期时间')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        subject = resolve_user(db, user_ref)
        current = db.execute('SELECT expires_at FROM members WHERE subject=?', (subject,)).fetchone()
        previous = current['expires_at'] if current else None
        if previous != data.expected_expires_at:
            raise HTTPException(409, '会员状态已发生变化，请刷新后重试')
        if data.mode == 'set':
            expiry = parse_expiry(data.new_expires_at)
        else:
            from miniapp_payment import plus_calendar_months
            now = datetime.now(timezone.utc)
            old = parse_expiry(previous) if previous else now
            try:
                expiry = plus_calendar_months(max(now, old), data.months)
            except (ValueError, OverflowError):
                raise HTTPException(400, '延长后的日期超出范围')
        updated = expiry.isoformat()
        now_iso = datetime.now(timezone.utc).isoformat()
        db.execute('INSERT INTO members(subject,expires_at) VALUES (?,?) ON CONFLICT(subject) DO UPDATE SET expires_at=excluded.expires_at', (subject, updated))
        db.execute('''INSERT INTO member_adjustments(subject,previous_expires_at,new_expires_at,reason,source,created_at)
            VALUES (?,?,?,?,?,?)''', (subject, previous, updated, reason, 'admin', now_iso))
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('adjust_member', user_ref, f'{previous or "无"} → {updated}；{reason}', now_iso))
    return {'user_ref': user_ref, 'expires_at': updated}


@app.get('/api/refund-requests', dependencies=[Depends(require_admin)])
def list_refund_requests(page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=100),
                         state: Literal['pending', 'closed', 'all'] = 'pending'):
    where = " WHERE r.status IN ('submitted', 'processing')" if state == 'pending' else (" WHERE r.status = 'closed'" if state == 'closed' else '')
    with database() as db:
        total = db.execute('SELECT COUNT(*) FROM refund_requests r' + where).fetchone()[0]
        rows = db.execute('''SELECT r.id, r.order_no, r.reason, r.status, r.response, r.admin_note,
            r.created_at, r.updated_at, o.plan_name, o.price_fen, o.status AS order_status
            FROM refund_requests r JOIN orders o ON o.order_no = r.order_no''' + where +
            ' ORDER BY r.id DESC LIMIT ? OFFSET ?', (page_size, (page - 1) * page_size)).fetchall()
    return {'requests': [dict(row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


class RefundRequestUpdate(BaseModel):
    status: Literal['processing', 'closed']
    response: str = Field(default='', max_length=200)
    note: str = Field(min_length=2, max_length=200)


@app.post('/api/refund-requests/{request_id}/update', dependencies=[Depends(require_admin)])
def update_refund_request(request_id: int, data: RefundRequestUpdate):
    response, note = data.response.strip(), data.note.strip()
    if len(note) < 2 or (data.status == 'closed' and len(response) < 2):
        raise HTTPException(400, '请填写内部处理记录；结束申请时还需填写给用户的说明')
    now = datetime.now(timezone.utc).isoformat()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT order_no, status FROM refund_requests WHERE id = ?', (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, '退款申请不存在')
        if row['status'] not in ('submitted', 'processing'):
            raise HTTPException(409, '退款申请已处理，请刷新后查看')
        db.execute('UPDATE refund_requests SET status = ?, response = ?, admin_note = ?, updated_at = ? WHERE id = ?',
                   (data.status, response, note, now, request_id))
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('update_refund_request', row['order_no'], f"申请 #{request_id}；{data.status}；{note}；用户说明：{response}", now))
    return {'ok': True}


@app.get('/api/review-events', dependencies=[Depends(require_admin)])
def review_events(page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=100),
                  state: Literal['pending', 'resolved', 'all'] = 'pending'):
    where = " WHERE state IN ('manual_review', 'refund_failed', 'unhandled')" if state == 'pending' else (" WHERE state = 'resolved'" if state == 'resolved' else '')
    with database() as db:
        total = db.execute('SELECT COUNT(*) FROM payment_events' + where).fetchone()[0]
        rows = db.execute('SELECT event_key, order_no, event_type, state, created_at, details FROM payment_events' + where +
                          ' ORDER BY created_at DESC LIMIT ? OFFSET ?', (page_size, (page - 1) * page_size)).fetchall()
    return {'events': [dict(row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


@app.get('/api/orders/{order_no}', dependencies=[Depends(require_admin)])
def order_detail(order_no: str):
    with database() as db:
        order = db.execute('''SELECT order_no, substr(subject,1,16) AS user_ref, plan_name, months, price_fen,
            status, created_at, updated_at, expires_at, product_id, platform_order_id, channel_order_id,
            review_needed, notify_needed FROM orders WHERE order_no=?''', (order_no,)).fetchone()
        if not order:
            raise HTTPException(404, '订单不存在')
        grant = db.execute('SELECT start_at, expires_at, created_at FROM membership_grants WHERE order_no=?', (order_no,)).fetchone()
        events = db.execute('SELECT event_type, state, created_at, details FROM payment_events WHERE order_no=? ORDER BY created_at DESC LIMIT 100', (order_no,)).fetchall()
    return {'order': dict(order), 'grant': dict(grant) if grant else None, 'events': [dict(row) for row in events]}


@app.get('/api/audit', dependencies=[Depends(require_admin)])
def audit(page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=100)):
    with database() as db:
        total = db.execute('SELECT COUNT(*) FROM admin_audit').fetchone()[0]
        rows = db.execute('SELECT id, action, target, details, created_at FROM admin_audit ORDER BY id DESC LIMIT ? OFFSET ?',
                          (page_size, (page - 1) * page_size)).fetchall()
    return {'records': [dict(row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


class SettingsInput(BaseModel):
    refresh_seconds: Literal[0, 15, 30, 60, 120]
    page_size: Literal[10, 20, 50]


@app.get('/api/settings', dependencies=[Depends(require_admin)])
def get_settings():
    with database() as db:
        values = {row['key']: row['value'] for row in db.execute("SELECT key, value FROM settings WHERE key IN ('admin_refresh_seconds','admin_page_size')")}
    try:
        result = SettingsInput(refresh_seconds=int(values.get('admin_refresh_seconds', 30)), page_size=int(values.get('admin_page_size', 20)))
    except (ValueError, TypeError):
        result = SettingsInput(refresh_seconds=30, page_size=20)
    return {'refresh_seconds': result.refresh_seconds, 'page_size': result.page_size}


@app.put('/api/settings', dependencies=[Depends(require_admin)])
def update_settings(data: SettingsInput):
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        db.executemany('INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                       [('admin_refresh_seconds', str(data.refresh_seconds)), ('admin_page_size', str(data.page_size))])
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('update_settings', 'admin', f'自动刷新 {data.refresh_seconds} 秒；每页 {data.page_size} 条', datetime.now(timezone.utc).isoformat()))
    return {'refresh_seconds': data.refresh_seconds, 'page_size': data.page_size}


class ReviewInput(BaseModel):
    order_no: str = Field(min_length=1, max_length=128)
    note: str = Field(min_length=1, max_length=200)
    new_expires_at: Optional[str] = Field(default=None, max_length=40)
    expected_expires_at: Optional[str] = Field(default=None, max_length=40)


class EventNoteInput(BaseModel):
    note: str = Field(min_length=2, max_length=200)


@app.post('/api/review-events/{event_key}/acknowledge', dependencies=[Depends(require_admin)])
def acknowledge_event(event_key: str, data: EventNoteInput):
    note = data.note.strip()
    if not re.fullmatch(r'[a-f0-9]{64}', event_key) or len(note) < 2:
        raise HTTPException(400, '请填写核查记录')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        event = db.execute("SELECT * FROM payment_events WHERE event_key=? AND state IN ('refund_failed', 'unhandled')", (event_key,)).fetchone()
        if not event:
            raise HTTPException(409, '事件状态已变化，请刷新后重试')
        db.execute("UPDATE payment_events SET state='resolved', details=? WHERE event_key=?",
                   ((event['details'] + '；人工核查：' + note)[:600], event_key))
        if event['order_no']:
            other = db.execute("SELECT 1 FROM payment_events WHERE order_no=? AND state IN ('manual_review','refund_failed','unhandled') LIMIT 1", (event['order_no'],)).fetchone()
            if not other:
                db.execute('UPDATE orders SET review_needed=0, updated_at=? WHERE order_no=?',
                           (datetime.now(timezone.utc).isoformat(), event['order_no']))
        db.execute('INSERT INTO admin_audit(action,target,details,created_at) VALUES (?,?,?,?)',
                   ('acknowledge_event', event['order_no'] or event_key[:16], note, datetime.now(timezone.utc).isoformat()))
    return {'ok': True}


@app.post('/api/refund-events/{event_key}/resolve', dependencies=[Depends(require_admin)])
def resolve_refund(event_key: str, data: ReviewInput):
    if not re.fullmatch(r'[a-f0-9]{64}', event_key) or not data.note.strip():
        raise HTTPException(400, '请填写核对记录')
    expiry = None
    if data.new_expires_at:
        expiry = parse_expiry(data.new_expires_at).isoformat()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        event = db.execute("SELECT * FROM payment_events WHERE event_key = ? AND event_type IN ('xpay_refund_notify', 'order_verification', 'xpay_goods_deliver_notify') AND state = 'manual_review'", (event_key,)).fetchone()
        if not event or (event['order_no'] and event['order_no'] != data.order_no):
            raise HTTPException(409, '核对事件状态或订单不匹配')
        order = db.execute('SELECT * FROM orders WHERE order_no = ?', (data.order_no,)).fetchone()
        if not order:
            raise HTTPException(404, '订单不存在')
        adjustment = '未调整会员到期时间'
        if expiry:
            member = db.execute('SELECT expires_at FROM members WHERE subject = ?', (order['subject'],)).fetchone()
            if not member:
                raise HTTPException(409, '该订单用户没有可调整的会员记录')
            if member['expires_at'] != data.expected_expires_at:
                raise HTTPException(409, '会员到期时间已变化或未核对，请重新读取后处理')
            db.execute('UPDATE members SET expires_at = ? WHERE subject = ?', (expiry, order['subject']))
            adjustment = f"会员到期时间由 {member['expires_at']} 调整为 {expiry}"
            db.execute('''INSERT INTO member_adjustments(subject,previous_expires_at,new_expires_at,reason,source,created_at)
                VALUES (?,?,?,?,?,?)''', (order['subject'], member['expires_at'], expiry, data.note.strip(),
                                          'refund_review', datetime.now(timezone.utc).isoformat()))
        db.execute("UPDATE payment_events SET order_no = ?, state = 'resolved', details = ? WHERE event_key = ?",
                   (data.order_no, (event['details'] + '；人工记录：' + data.note.strip())[:600], event_key))
        other = db.execute("SELECT 1 FROM payment_events WHERE order_no = ? AND state IN ('manual_review', 'refund_failed', 'unhandled') LIMIT 1", (data.order_no,)).fetchone()
        if not other:
            db.execute('UPDATE orders SET review_needed = 0, updated_at = ? WHERE order_no = ?', (datetime.now(timezone.utc).isoformat(), data.order_no))
        db.execute('INSERT INTO admin_audit (action, target, details, created_at) VALUES (?, ?, ?, ?)',
                   ('resolve_refund', data.order_no, f'{adjustment}；{data.note.strip()}', datetime.now(timezone.utc).isoformat()))
    return {'ok': True}


@app.post('/api/orders/{order_no}/refresh', dependencies=[Depends(require_admin)])
def admin_refresh_order(order_no: str):
    from miniapp_payment import query_platform_order
    with database() as db:
        order = db.execute('SELECT product_id FROM orders WHERE order_no = ?', (order_no,)).fetchone()
    if not order:
        raise HTTPException(404, '订单不存在')
    if not order['product_id']:
        raise HTTPException(409, '订单未关联微信商品，无法查单')
    query_platform_order(order_no)
    with database() as db:
        db.execute('INSERT INTO admin_audit (action, target, details, created_at) VALUES (?, ?, ?, ?)',
                   ('refresh_order', order_no, '管理员查询微信订单状态', datetime.now(timezone.utc).isoformat()))
    return {'ok': True}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=ADMIN_PORT, access_log=False, proxy_headers=False)
