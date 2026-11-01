"""WeChat Mini Program content safety integration.

The image APIs in this project are not a public publishing feed, but users do
upload photographs.  Every image is checked before the Hivision pipeline is
allowed to run.  Only audit metadata is retained locally; the original image,
access token and AppSecret are never written to disk or logs.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps

from fastapi import HTTPException


WECHAT_API = "https://api.weixin.qq.com"
IMAGE_CHECK_URL = WECHAT_API + "/wxa/img_sec_check"
TEXT_CHECK_URL = WECHAT_API + "/wxa/msg_sec_check"
MEDIA_CHECK_URL = WECHAT_API + "/wxa/media_check_async"

# The legacy synchronous image endpoint is documented with a 1 MB limit.  A
# normalized JPEG is sent so PNG/WebP uploads and camera originals work too.
MAX_CHECK_IMAGE_BYTES = 1024 * 1024
MAX_TEXT_LENGTH = 2500
TOKEN_REFRESH_SKEW = 120
MAX_AUDIT_BYTES = 5 * 1024 * 1024
AUDIT_BACKUPS = 2

_token_lock = threading.Lock()
_access_token = ""
_access_token_expires_at = 0.0
_audit_lock = threading.Lock()


class ContentSecurityUnavailable(RuntimeError):
    """Raised when WeChat cannot be reached or the credentials are invalid."""


def _flag(name: str, default: bool = True) -> bool:
    value = os.environ.get(name, "true" if default else "false").strip().lower()
    if value not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return value == "true"


def enabled() -> bool:
    return _flag("IDPHOTO_CONTENT_SECURITY_ENABLED", True)


def configured() -> bool:
    return bool(os.environ.get("WECHAT_APP_ID") and os.environ.get("WECHAT_APP_SECRET"))


def configuration_state() -> tuple[str, str]:
    """Return a safe status tuple without making an external request."""
    try:
        if not enabled():
            return "disabled", "内容安全检查已关闭"
    except RuntimeError:
        return "unavailable", "内容安全检查配置无效"
    if not configured():
        return "unavailable", "缺少微信内容安全凭据"
    return "ok", "已配置微信图片、文本和媒体内容安全检查"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value, limit=240) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\r", " ").replace("\n", " ")[:limit]


def _audit_dir() -> Path:
    root = Path(os.environ.get("IDPHOTO_DATA_DIR", Path(__file__).resolve().parent / ".miniapp_data"))
    directory = root / "content_security"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    return directory


def _audit(record: dict) -> None:
    # JSONL is intentionally metadata-only.  Never add request body, OpenID,
    # token or secret here.
    allowed = {
        "checked_at", "kind", "sha256", "subject", "errcode", "errmsg",
        "trace_id", "safe", "available", "media_type", "scene", "state",
    }
    clean = {key: record[key] for key in allowed if key in record}
    path = _audit_dir() / "audit.jsonl"
    line = (json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with _audit_lock:
        try:
            if path.exists() and path.stat().st_size + len(line) > MAX_AUDIT_BYTES:
                # Keep a small bounded audit trail.  API and push are separate
                # processes, so rotation is best effort; O_APPEND still keeps
                # individual metadata records intact when they race.
                for index in range(AUDIT_BACKUPS, 1, -1):
                    source = path.with_name(path.name + f".{index - 1}")
                    target = path.with_name(path.name + f".{index}")
                    if target.exists():
                        target.unlink(missing_ok=True)
                    if source.exists():
                        os.replace(source, target)
                if path.exists():
                    target = path.with_name(path.name + ".1")
                    target.unlink(missing_ok=True)
                    os.replace(path, target)
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(fd, line)
            finally:
                os.close(fd)
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        except OSError:
            # An audit write must never turn a safe image into a service error;
            # the service-status endpoint still exposes the external check.
            return


def _response_payload(response: requests.Response) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ContentSecurityUnavailable("微信内容安全服务返回无效数据") from exc
    if not isinstance(payload, dict):
        raise ContentSecurityUnavailable("微信内容安全服务返回无效数据")
    return payload


def _get_access_token(force: bool = False) -> str:
    global _access_token, _access_token_expires_at
    appid = os.environ.get("WECHAT_APP_ID", "")
    secret = os.environ.get("WECHAT_APP_SECRET", "")
    if not appid or not secret:
        raise ContentSecurityUnavailable("微信内容安全凭据未配置")
    now = time.monotonic()
    with _token_lock:
        if not force and _access_token and now < _access_token_expires_at:
            return _access_token
        try:
            response = requests.get(
                WECHAT_API + "/cgi-bin/token",
                params={"grant_type": "client_credential", "appid": appid, "secret": secret},
                timeout=8,
            )
            response.raise_for_status()
            payload = _response_payload(response)
        except (requests.RequestException, ContentSecurityUnavailable) as exc:
            raise ContentSecurityUnavailable("微信接口调用凭据暂不可用") from exc
        token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not isinstance(token, str) or not token or not isinstance(expires_in, (int, float)):
            raise ContentSecurityUnavailable("微信接口调用凭据获取失败")
        _access_token = token
        _access_token_expires_at = time.monotonic() + max(60.0, float(expires_in) - TOKEN_REFRESH_SKEW)
        return token


def _post_json(url: str, payload: dict, force_token=False) -> dict:
    token = _get_access_token(force=force_token)
    try:
        response = requests.post(url, params={"access_token": token}, json=payload, timeout=12)
        response.raise_for_status()
        return _response_payload(response)
    except (requests.RequestException, ContentSecurityUnavailable) as exc:
        raise ContentSecurityUnavailable("微信内容安全服务暂不可用") from exc


def _normalized_jpeg(image_bytes: bytes) -> bytes:
    """Create a bounded JPEG accepted by the synchronous image API."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            # The legacy synchronous endpoint documents a 750x1334 pixel
            # limit.  Normalize to that bound before sending camera originals.
            image.thumbnail((750, 1334), Image.Resampling.LANCZOS)
            quality = 86
            while quality >= 35:
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=quality, optimize=True)
                data = buffer.getvalue()
                if len(data) <= MAX_CHECK_IMAGE_BYTES:
                    return data
                quality -= 8
            # Keep shrinking only when a very detailed photo still exceeds the
            # documented limit at the lowest quality.  The bounded loop also
            # prevents a pathological image from creating an endless resize.
            for _ in range(8):
                next_size = (max(128, image.width * 3 // 4), max(128, image.height * 3 // 4))
                if next_size == image.size:
                    break
                image.thumbnail(next_size, Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=45, optimize=True)
                data = buffer.getvalue()
                if len(data) <= MAX_CHECK_IMAGE_BYTES:
                    return data
    except (OSError, ValueError) as exc:
        raise ContentSecurityUnavailable("图片无法转换为内容安全检查格式") from exc
    raise ContentSecurityUnavailable("图片过大，无法提交内容安全检查")


def _post_image(image_bytes: bytes, force_token=False) -> dict:
    token = _get_access_token(force=force_token)
    normalized = _normalized_jpeg(image_bytes)
    try:
        response = requests.post(
            IMAGE_CHECK_URL,
            params={"access_token": token},
            files={"media": ("content-security.jpg", normalized, "image/jpeg")},
            timeout=20,
        )
        response.raise_for_status()
        return _response_payload(response)
    except (requests.RequestException, ContentSecurityUnavailable) as exc:
        raise ContentSecurityUnavailable("微信图片内容安全服务暂不可用") from exc


def _retry_on_expired_token(call):
    try:
        payload = call(False)
    except ContentSecurityUnavailable:
        raise
    if payload.get("errcode") == 40001:
        return call(True)
    return payload


def _result(
    *, kind: str, digest: str = "", subject: str | None = None,
    payload: dict | None = None, available: bool = True, safe: bool | None = None,
    media_type: int | None = None, scene: int | None = None,
) -> dict:
    payload = payload or {}
    errcode = payload.get("errcode")
    if not isinstance(errcode, int):
        errcode = -1 if not available else 0
    errmsg = _safe_text(payload.get("errmsg") or ("ok" if available else "内容安全服务暂不可用"), 160)
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    suggestion = result.get("suggest")
    if safe is None and available and errcode == 0 and kind != "media":
        safe = suggestion != "risky" if suggestion else True
    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id:
        trace_id = ""
    data = {
        "safe": bool(safe) if safe is not None else None,
        "available": available,
        "errcode": errcode,
        "errmsg": errmsg,
        "trace_id": trace_id,
        "sha256": digest,
        "checked_at": _now(),
    }
    _audit({
        "checked_at": data["checked_at"], "kind": kind, "sha256": digest,
        "subject": subject or "", "errcode": errcode, "errmsg": errmsg,
        "trace_id": trace_id, "safe": data["safe"], "available": available,
        "media_type": media_type, "scene": scene,
        "state": "pass" if data["safe"] is True else "risk" if data["safe"] is False else "unavailable",
    })
    return data


async def check_image(image_bytes: bytes, subject: str | None = None) -> dict:
    digest = hashlib.sha256(image_bytes).hexdigest()
    try:
        is_enabled = enabled()
    except RuntimeError:
        return _result(kind="image", digest=digest, subject=subject, available=False, safe=None)
    if not is_enabled:
        return _result(kind="image", digest=digest, subject=subject, available=True, safe=True,
                       payload={"errcode": 0, "errmsg": "content security disabled"})
    if not configured():
        return _result(kind="image", digest=digest, subject=subject, available=False, safe=None)
    try:
        payload = await asyncio.to_thread(
            _retry_on_expired_token, lambda force: _post_image(image_bytes, force)
        )
    except (ContentSecurityUnavailable, RuntimeError):
        return _result(kind="image", digest=digest, subject=subject, available=False, safe=None)
    errcode = payload.get("errcode")
    if errcode == 87014:
        return _result(kind="image", digest=digest, subject=subject, payload=payload, safe=False)
    if errcode != 0:
        return _result(kind="image", digest=digest, subject=subject, payload=payload, available=False, safe=None)
    # The legacy img_sec_check response is only {errcode: 0, errmsg: ok}.
    # Newer responses may include a structured result; if it is present, only
    # an explicit pass is accepted.  Unknown structured responses fail closed.
    if "result" not in payload and "detail" not in payload:
        safe = True
    else:
        image_result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        safe = image_result.get("suggest") == "pass"
    return _result(kind="image", digest=digest, subject=subject, payload=payload, safe=safe)


async def check_text(content: str, openid: str, *, scene: int = 2, title: str = "", subject: str | None = None) -> dict:
    if len(content) > MAX_TEXT_LENGTH:
        raise HTTPException(413, "待检测文本不能超过2500字")
    try:
        is_enabled = enabled()
    except RuntimeError:
        return _result(kind="text", subject=subject, available=False, safe=None, scene=scene)
    if not is_enabled:
        return _result(kind="text", subject=subject, available=True, safe=True,
                       payload={"errcode": 0, "errmsg": "content security disabled"}, scene=scene)
    if not configured():
        return _result(kind="text", subject=subject, available=False, safe=None, scene=scene)
    body = {"content": content, "version": 2, "scene": scene, "openid": openid}
    if title:
        body["title"] = title[:100]
    try:
        payload = await asyncio.to_thread(_retry_on_expired_token, lambda force: _post_json(TEXT_CHECK_URL, body, force))
    except (ContentSecurityUnavailable, RuntimeError):
        return _result(kind="text", subject=subject, available=False, safe=None, scene=scene)
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    if payload.get("errcode") == 87014:
        return _result(kind="text", subject=subject, payload=payload, safe=False, scene=scene)
    if payload.get("errcode") != 0:
        return _result(kind="text", subject=subject, payload=payload, available=False, safe=None, scene=scene)
    # A missing or unknown suggestion must not be treated as a pass.
    safe = result.get("suggest") == "pass"
    return _result(kind="text", subject=subject, payload=payload, safe=safe, scene=scene)


async def check_media(media_url: str, openid: str, *, media_type: int = 2, scene: int = 4, subject: str | None = None) -> dict:
    parsed = urlparse(media_url)
    if parsed.scheme != "https" or not parsed.netloc or len(media_url) > 2048:
        raise HTTPException(400, "媒体地址必须是可公开访问的 HTTPS 地址")
    if media_type not in (1, 2):
        raise HTTPException(400, "媒体类型仅支持音频或图片")
    try:
        is_enabled = enabled()
    except RuntimeError:
        return _result(kind="media", subject=subject, available=False, safe=None, media_type=media_type, scene=scene)
    if not is_enabled:
        return _result(kind="media", subject=subject, available=True, safe=True,
                       payload={"errcode": 0, "errmsg": "content security disabled"}, media_type=media_type, scene=scene)
    if not configured():
        return _result(kind="media", subject=subject, available=False, safe=None, media_type=media_type, scene=scene)
    body = {"media_url": media_url, "media_type": media_type, "version": 2, "scene": scene, "openid": openid}
    try:
        payload = await asyncio.to_thread(_retry_on_expired_token, lambda force: _post_json(MEDIA_CHECK_URL, body, force))
    except (ContentSecurityUnavailable, RuntimeError):
        return _result(kind="media", subject=subject, available=False, safe=None, media_type=media_type, scene=scene)
    # This endpoint only accepts the job.  The final verdict arrives through
    # the configured WeChat message push callback.
    result = _result(kind="media", subject=subject, payload=payload,
                     available=payload.get("errcode") == 0, safe=None,
                     media_type=media_type, scene=scene)
    result["accepted"] = payload.get("errcode") == 0
    result["safe"] = None
    return result


def record_media_event(event: dict) -> None:
    """Record an async WeChat media verdict without retaining media content."""
    if not isinstance(event, dict):
        return
    result = event.get("result") if isinstance(event.get("result"), dict) else {}
    status_code = event.get("status_code")
    # Older callback payloads use isrisky; newer v2 payloads include result.
    normalized_status = status_code
    try:
        if normalized_status is not None:
            normalized_status = int(normalized_status)
    except (TypeError, ValueError):
        normalized_status = -1
    raw_errcode = event.get("errcode")
    try:
        errcode = int(raw_errcode) if raw_errcode is not None else normalized_status
    except (TypeError, ValueError):
        errcode = -1
    if errcode is None:
        errcode = -1
    if normalized_status not in (None, 0) or errcode != 0:
        # Download failures (notably -1008) and other callback errors take
        # precedence over an optimistic isrisky field.
        safe = None
        state = "unavailable"
    elif "isrisky" in event:
        safe = event.get("isrisky") in (0, "0", False)
        state = "pass" if safe else "risk"
    elif result.get("suggest") in {"pass", "risky", "review"}:
        safe = result.get("suggest") == "pass"
        state = "pass" if safe else "risk"
    elif errcode == 0 and normalized_status in (None, 0):
        safe = None
        state = "accepted"
    else:
        safe = None
        state = "unavailable"
    _audit({
        "checked_at": _now(), "kind": "media_callback", "subject": "",
        "errcode": errcode, "errmsg": _safe_text(event.get("errmsg", "")),
        "trace_id": _safe_text(event.get("trace_id", ""), 120),
        "safe": safe, "available": state != "unavailable",
        "media_type": event.get("media_type", 2), "scene": None,
        "state": state,
    })


def security_error(result: dict) -> HTTPException:
    trace = result.get("trace_id") if isinstance(result.get("trace_id"), str) else ""
    suffix = f"（检测编号：{trace[:40]}）" if trace else ""
    if not result.get("available"):
        return HTTPException(503, "内容安全检测服务暂不可用，请稍后重试" + suffix)
    return HTTPException(400, "图片未通过内容安全检测，请更换照片" + suffix)
