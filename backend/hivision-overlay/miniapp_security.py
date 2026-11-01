"""Security boundary for the WeChat mini-program API (single-process deployment)."""
import asyncio
import base64
import contextvars
import hashlib
import hmac
import io
import json
import os
import time
from collections import defaultdict, deque

import cv2
import numpy as np
import requests
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from miniapp_content_security import check_image, security_error

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_BODY_BYTES = 28 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
TOKEN_LIFETIME = 3600

_request_subject = contextvars.ContextVar('miniapp_request_subject', default=None)

# These routes are intentionally public: health/status are read-only, the
# payment callback verifies its own WeChat signature, and the demo media is a
# fixed one-pixel image used only as the media_check_async review example.
PUBLIC_PATHS = frozenset({
    '/health', '/service-status', '/auth/wechat', '/payment/notify',
    '/content-security/demo-media',
})


def auth_enabled():
    value = os.environ.get('IDPHOTO_AUTH_REQUIRED', 'true').lower()
    if value not in ('true', 'false'):
        raise RuntimeError('IDPHOTO_AUTH_REQUIRED must be true or false')
    return value == 'true'


def validate_config():
    if auth_enabled():
        if not os.environ.get('WECHAT_APP_ID') or not os.environ.get('WECHAT_APP_SECRET'):
            raise RuntimeError('WECHAT_APP_ID and WECHAT_APP_SECRET are required')
        if len(os.environ.get('IDPHOTO_TOKEN_SECRET', '')) < 32:
            raise RuntimeError('IDPHOTO_TOKEN_SECRET must contain at least 32 characters')


def _encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _decode(data):
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


def subject_for_openid(openid):
    return hmac.new(os.environ['IDPHOTO_TOKEN_SECRET'].encode(), openid.encode(), hashlib.sha256).hexdigest()


def issue_token(openid):
    secret = os.environ['IDPHOTO_TOKEN_SECRET'].encode()
    subject = subject_for_openid(openid)
    payload = _encode(json.dumps({'sub': subject, 'exp': int(time.time()) + TOKEN_LIFETIME}, separators=(',', ':')).encode())
    signature = _encode(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
    return payload + '.' + signature


def verify_token(token):
    try:
        if len(token) > 1024:
            return None
        payload, signature = token.split('.')
        expected = _encode(hmac.new(os.environ['IDPHOTO_TOKEN_SECRET'].encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_decode(payload))
        if not isinstance(data.get('sub'), str) or len(data['sub']) != 64 or not isinstance(data.get('exp'), int) or data['exp'] <= time.time():
            return None
        return data['sub']
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        return None


class LoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


async def exchange_wechat_code(code):
    def exchange():
        return requests.get('https://api.weixin.qq.com/sns/jscode2session', params={
            'appid': os.environ['WECHAT_APP_ID'], 'secret': os.environ['WECHAT_APP_SECRET'],
            'js_code': code, 'grant_type': 'authorization_code',
        }, timeout=8)
    try:
        response = await asyncio.to_thread(exchange)
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        raise HTTPException(503, '微信登录服务暂不可用')
    if not isinstance(result, dict) or not isinstance(result.get('openid'), str) or not result['openid']:
        raise HTTPException(401, '微信登录失败，请重新登录')
    return result


async def wechat_login(data: LoginRequest):
    if not auth_enabled():
        raise HTTPException(404, '登录服务未启用')
    result = await exchange_wechat_code(data.code)
    from miniapp_identity import bind_identity
    await asyncio.to_thread(bind_identity, result['openid'], subject_for_openid(result['openid']))
    return {'token': issue_token(result['openid']), 'expires_in': TOKEN_LIFETIME}


async def read_image(upload: UploadFile, encoded: str, mode=cv2.IMREAD_COLOR):
    image, _ = await read_image_with_security(upload, encoded, mode)
    return image


async def _read_image_bytes(upload: UploadFile, encoded: str):
    if encoded:
        try:
            raw = encoded.split(',', 1)[1] if encoded.startswith('data:image/') else encoded
            if len(raw) > ((MAX_IMAGE_BYTES + 2) // 3) * 4:
                raise HTTPException(413, '图片不能超过20MB')
            image_bytes = base64.b64decode(raw, validate=True)
        except (ValueError, IndexError):
            raise HTTPException(400, '图片数据无效')
    elif upload:
        image_bytes = await upload.read(MAX_IMAGE_BYTES + 1)
    else:
        raise HTTPException(400, '请选择图片')
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(413, '图片不能超过20MB')
    return image_bytes


def _decode_image(image_bytes, mode):
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise HTTPException(415, '仅支持JPG、PNG或WebP图片')
            width, height = image.size
            if width < 1 or height < 1 or width > 8192 or height > 8192 or width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(413, '图片尺寸过大，请压缩后重试')
            image.verify()
        decoded = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), mode)
        if decoded is None:
            raise ValueError('decode failed')
        return decoded
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(400, '图片无效或已损坏')


async def read_image_with_security(upload: UploadFile, encoded: str, mode=cv2.IMREAD_COLOR):
    """Read, validate and check an uploaded image before any inference."""
    image_bytes = await _read_image_bytes(upload, encoded)
    decoded = _decode_image(image_bytes, mode)
    result = await check_image(image_bytes, _request_subject.get())
    if result.get('safe') is not True:
        raise security_error(result)
    return decoded, result


async def audit_image(upload: UploadFile, encoded: str, mode=cv2.IMREAD_UNCHANGED):
    """Validate an image and return its safety result without fail-closed blocking.

    This is used only by the review/demo endpoint.  Production processing
    routes must continue to use :func:`read_image_with_security`, which rejects
    a risky or unavailable check before inference.
    """
    image_bytes = await _read_image_bytes(upload, encoded)
    _decode_image(image_bytes, mode)
    return await check_image(image_bytes, _request_subject.get())


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.hits = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = {k.lower(): v for k, v in scope.get('headers', [])}
        path = scope['path']
        client = scope.get('client')
        ip = client[0] if client else 'unknown'
        if os.environ.get('IDPHOTO_TRUST_CLOUDFLARE', 'false').lower() == 'true' and ip in ('127.0.0.1', '::1'):
            ip = headers.get(b'cf-connecting-ip', b'').decode('ascii', 'ignore')[:64] or ip
        subject = None
        if auth_enabled() and path not in PUBLIC_PATHS:
            auth = headers.get(b'authorization', b'').decode('ascii', 'ignore')
            subject = verify_token(auth[7:]) if auth.startswith('Bearer ') else None
            if not subject:
                return await JSONResponse({'detail': '请先登录'}, status_code=401)(scope, receive, send)
        scope.setdefault('state', {})['subject'] = subject
        if path != '/health':
            key = ('login:' + ip) if path == '/auth/wechat' else ('user:' + subject if subject else 'ip:' + ip)
            now = time.monotonic()
            # Bound inactive key storage as well as each window.
            if len(self.hits) > 10000:
                for old_key, queue in list(self.hits.items()):
                    if not queue or now - queue[-1] >= 60:
                        del self.hits[old_key]
                if len(self.hits) > 10000 and key not in self.hits:
                    return await JSONResponse({'detail': '服务繁忙，请稍后重试'}, status_code=429)(scope, receive, send)
            queue = self.hits[key]
            while queue and now - queue[0] >= 60:
                queue.popleft()
            limit = 30 if path == '/auth/wechat' else 60
            if len(queue) >= limit:
                return await JSONResponse({'detail': '操作过于频繁，请稍后再试'}, status_code=429, headers={'Retry-After': '60'})(scope, receive, send)
            queue.append(now)
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await JSONResponse({'detail': '请求长度无效'}, status_code=400)(scope, receive, send)
        if length < 0 or length > MAX_BODY_BYTES:
            return await JSONResponse({'detail': '请求过大'}, status_code=413)(scope, receive, send)
        chunks = []
        total = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            total += len(chunk)
            if total > MAX_BODY_BYTES:
                return await JSONResponse({'detail': '请求过大'}, status_code=413)(scope, receive, send)
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        body = b''.join(chunks)
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {'type': 'http.request', 'body': body, 'more_body': False}
        subject_token = _request_subject.set(subject)
        try:
            return await self.app(scope, replay, send)
        finally:
            _request_subject.reset(subject_token)
