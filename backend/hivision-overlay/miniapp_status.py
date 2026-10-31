"""Small, privacy-preserving health summary for the mini-program.

The checks describe what is actually observed; they do not make a test image
or payment, and an API timeout cannot distinguish an outage from a bad network.
"""
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter
from starlette.responses import JSONResponse

from hivision.creator.human_matting import WEIGHTS
from miniapp_membership import DB_PATH
from miniapp_payment import payment_enabled
from miniapp_telemetry import writer as metrics_writer

router = APIRouter()
FAILURE_WINDOW_SECONDS = 300
TRACKED_PATHS = {
    '/idphoto': 'photo', '/human_matting': 'matting', '/idphoto_crop': 'photo',
    '/convert_image': 'tools', '/add_background': 'tools',
    '/generate_layout_photos': 'tools', '/watermark': 'tools', '/set_kb': 'tools',
    '/auth/wechat': 'login', '/membership/status': 'membership',
    '/membership/plans': 'membership',
}


class RecentFailures:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.failed_at = {}

    def observe(self, path, status):
        if path not in TRACKED_PATHS:
            return
        with self.lock:
            if status >= 500:
                self.failed_at[path] = self.clock()
            elif 200 <= status < 300:
                self.failed_at.pop(path, None)

    def groups(self):
        now = self.clock()
        with self.lock:
            self.failed_at = {path: at for path, at in self.failed_at.items()
                              if now - at < FAILURE_WINDOW_SECONDS}
            return {TRACKED_PATHS[path] for path in self.failed_at}


failures = RecentFailures()


class ServiceObservationMiddleware:
    """Observe only the result code of known routes; never log request data."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('path') not in TRACKED_PATHS:
            return await self.app(scope, receive, send)
        path = scope['path']
        observed = False
        code = 500
        started = time.monotonic()

        async def observe_send(message):
            nonlocal observed, code
            if message['type'] == 'http.response.start':
                code = message['status']
                failures.observe(path, code)
                observed = True
            await send(message)

        try:
            await self.app(scope, receive, observe_send)
        except Exception:
            if not observed:
                failures.observe(path, 500)
            raise
        finally:
            try:
                metrics_writer.record(path, code, (time.monotonic() - started) * 1000)
            except Exception:
                pass  # Monitoring is never allowed to interrupt a request.


def membership_database_ready():
    if not DB_PATH.is_file():
        return False
    try:
        # Read-only and bounded: a status check must never create or migrate data.
        uri = 'file:' + quote(str(DB_PATH)) + '?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=0.3) as db:
            return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='members'").fetchone())
    except sqlite3.Error:
        return False


def status_snapshot(sandbox=False):
    recent = failures.groups()
    model_ready = Path(WEIGHTS['birefnet-v1-lite']).is_file()
    matting_ready = Path(WEIGHTS['modnet_photographic_portrait_matting']).is_file()
    optional_models_ready = all(Path(WEIGHTS[name]).is_file() for name in ('birefnet-v1-lite', 'hivision_modnet', 'modnet_photographic_portrait_matting'))
    database_ready = membership_database_ready()
    checks = [
        {'id': 'connection', 'name': '服务连接', 'state': 'ok', 'detail': '已连接到照片服务'},
        {'id': 'photo', 'name': '证件照制作',
         'state': 'unavailable' if not model_ready else ('degraded' if 'photo' in recent else 'ok'),
         'detail': ('基础处理模型未就绪' if not model_ready else
                    '近期处理出现异常，请稍后重试' if 'photo' in recent else '基础模型已就绪，近期未发现异常')},
        {'id': 'matting', 'name': '人像抠图',
         'state': 'unavailable' if not matting_ready else ('degraded' if 'matting' in recent else 'ok'),
         'detail': ('默认人像模型未就绪' if not matting_ready else
                    '近期处理出现异常，请稍后重试' if 'matting' in recent else '默认模型已就绪，近期未发现异常')},
        {'id': 'models', 'name': '可选人像模型',
         'state': 'ok' if optional_models_ready else 'degraded',
         'detail': '页面提供的模型文件已就绪' if optional_models_ready else '部分可选模型未就绪，可尝试其他模型'},
        {'id': 'tools', 'name': '图片工具', 'state': 'degraded' if 'tools' in recent else 'ok',
         'detail': '近期处理出现异常，请稍后重试' if 'tools' in recent else '近期未发现异常'},
        {'id': 'login', 'name': '微信登录', 'state': 'degraded' if 'login' in recent else 'ok',
         'detail': '近期登录出现异常，请稍后重试' if 'login' in recent else '近期未发现异常'},
        {'id': 'membership', 'name': '会员状态',
         'state': 'unavailable' if not database_ready else ('degraded' if 'membership' in recent else 'ok'),
         'detail': ('会员数据暂不可用' if not database_ready else
                    '近期查询出现异常，请稍后重试' if 'membership' in recent else '会员数据可读取')},
        {'id': 'payment', 'name': '会员购买', 'state': 'unknown' if payment_enabled() else 'disabled',
         'detail': '购买功能已开启，支付结果以订单为准' if payment_enabled() else '暂未开放购买'},
    ]
    if sandbox:
        for item in checks:
            if item['id'] == 'connection':
                item['detail'] = '已连接到支付沙箱'
            if item['id'] in ('photo', 'matting', 'models', 'tools'):
                item.update(state='disabled', detail='支付沙箱未接入此功能')
        for item in checks:
            if item['id'] == 'payment':
                item['detail'] = '沙箱购买已开启，仅供测试' if payment_enabled() else '沙箱购买暂未开放'
    return {
        'status': 'degraded' if any(item['state'] in ('degraded', 'unavailable') for item in checks) else 'ok',
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'checks': checks,
        'note': ('当前为支付沙箱，未接入图片处理。' if sandbox else '') + '仅包含连接、基础配置与近期服务异常，不代表每次处理或第三方支付必然成功。',
    }


@router.get('/service-status')
def service_status():
    return JSONResponse(status_snapshot(), headers={'Cache-Control': 'no-store'})
