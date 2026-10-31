"""Temporary, isolated Android virtual-payment sandbox API."""
from contextlib import asynccontextmanager
from pathlib import Path
import threading

from fastapi import FastAPI
from starlette.responses import JSONResponse, PlainTextResponse

from miniapp_identity import identity_key
from miniapp_membership import DATA_DIR, database, initialize, router as membership_router
from miniapp_payment import payment_env, reconcile_loop, router as payment_router, validate_payment_config
from miniapp_security import SecurityMiddleware, validate_config, wechat_login
from miniapp_status import ServiceObservationMiddleware, status_snapshot


@asynccontextmanager
async def lifespan(app):
    expected = (Path(__file__).resolve().parent / '.miniapp_sandbox').resolve()
    if payment_env() != 1 or DATA_DIR.resolve() != expected:
        raise RuntimeError('沙箱服务必须使用独立的沙箱数据库和支付环境')
    validate_config()
    initialize()
    identity_key()
    validate_payment_config()
    with database() as db:
        db.execute("UPDATE plans SET name = '沙箱1个月会员', price_fen = 1, wechat_product_id = 'vip_sandbox_1fen', status = 'active' "
                   "WHERE months = 1 AND price_fen IN (1, 1200) AND wechat_product_id IN ('', 'vip_1m', 'vip_sandbox_1fen')")
        for months, fen, product in ((3, 2400, 'vip_3m'), (12, 6800, 'vip_12m')):
            db.execute("UPDATE plans SET wechat_product_id = ?, status = 'active' WHERE months = ? AND price_fen = ? AND wechat_product_id IN ('', ?)",
                       (product, months, fen, product))
    stop = threading.Event()
    worker = threading.Thread(target=reconcile_loop, args=(stop,), daemon=True, name='sandbox-reconcile')
    worker.start()
    try:
        yield
    finally:
        stop.set()


inner = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
inner.add_middleware(SecurityMiddleware)
inner.add_middleware(ServiceObservationMiddleware)
inner.post('/auth/wechat')(wechat_login)


@inner.get('/service-status')
def sandbox_service_status():
    return JSONResponse(status_snapshot(sandbox=True), headers={'Cache-Control': 'no-store'})

inner.include_router(membership_router)
inner.include_router(payment_router)


async def app(scope, receive, send):
    if scope['type'] == 'http':
        prefix = '/sandbox'
        if not scope.get('path', '').startswith(prefix + '/'):
            await PlainTextResponse('Not Found', status_code=404)(scope, receive, send)
            return
        scope = dict(scope)
        scope['path'] = scope['path'][len(prefix):]
        scope['raw_path'] = scope['path'].encode('utf-8')
    await inner(scope, receive, send)
