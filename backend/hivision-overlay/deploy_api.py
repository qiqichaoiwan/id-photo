from fastapi import FastAPI, UploadFile, Form, File, Query, HTTPException, Request
from typing import Optional
import asyncio
import inspect
from contextlib import asynccontextmanager
from pathlib import Path
from pydantic import BaseModel, Field
from miniapp_security import SecurityMiddleware, audit_image, read_image, read_image_with_security, validate_config, wechat_login
from miniapp_membership import initialize as initialize_membership, router as membership_router
from miniapp_identity import get_openid, identity_key, resolve_subject
from miniapp_payment import router as payment_router, reconcile_loop, validate_payment_config
from miniapp_status import ServiceObservationMiddleware, router as status_router
from miniapp_content_security import check_media, check_text, enabled as content_security_enabled
import threading
from hivision import IDCreator
from hivision.error import FaceError
from hivision.creator.layout_calculator import (
    generate_layout_array,
    generate_layout_image,
)
from hivision.creator.choose_handler import choose_handler
from hivision.creator.human_matting import WEIGHTS
from hivision.utils import (
    add_background,
    resize_image_to_kb,
    hex_to_rgb,
    add_watermark,
    save_image_dpi_to_bytes,
)
import base64
import io
from PIL import Image
import numpy as np
import cv2
from starlette.middleware.cors import CORSMiddleware
from starlette.formparsers import MultiPartParser
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

# Base64 form fields may be larger than the encoded image. The middleware
# limits the complete body; read_image separately validates the decoded image.
MultiPartParser.max_part_size = 28 * 1024 * 1024

# Starlette 0.52+ takes max_part_size as a keyword-only default on Request
# rather than reading MultiPartParser.max_part_size. FastAPI's generated
# UploadFile dependency calls request.form() without an override, so adjust
# that default to the same bounded request limit. Explicit caller limits are
# preserved. This keeps normal camera originals from being rejected at 1 MB
# before our image validation and content-safety check run.
_request_get_form = StarletteRequest._get_form
_request_get_form_parameters = inspect.signature(_request_get_form).parameters


async def _get_form_with_image_limit(self, *, max_files=1000, max_fields=1000, max_part_size=28 * 1024 * 1024):
    options = {
        'max_files': max_files,
        'max_fields': max_fields,
        'max_part_size': max_part_size,
    }
    # FastAPI 0.110 can resolve to older Starlette releases whose Request
    # parser does not expose max_part_size. Only pass parameters supported by
    # the installed version; the class-level parser limit above covers those
    # releases without the newer keyword.
    options = {key: value for key, value in options.items() if key in _request_get_form_parameters}
    return await _request_get_form(self, **options)


StarletteRequest._get_form = _get_form_with_image_limit

@asynccontextmanager
async def lifespan(app):
    validate_config()
    initialize_membership()
    identity_key()
    validate_payment_config()
    stop = threading.Event()
    worker = threading.Thread(target=reconcile_loop, args=(stop,), daemon=True, name='membership-reconcile')
    worker.start()
    try:
        yield
    finally:
        stop.set()

app = FastAPI(lifespan=lifespan)
creator = IDCreator()
# IDCreator stores its selected handlers on the instance. Keep model selection
# and inference together while the event loop remains free for status requests.
creator_lock = threading.Lock()


def run_creator(image, matting_model=None, face_model=None, **options):
    with creator_lock:
        choose_handler(creator, matting_model_option=matting_model, face_detect_option=face_model)
        return creator(image, **options)


def image_data_url(image_bytes):
    # resize_image_to_kb produces JPEG; other endpoints normally return PNG.
    mime = "image/jpeg" if image_bytes.startswith(b"\xff\xd8\xff") else "image/png"
    return f"data:{mime};base64," + base64.b64encode(image_bytes).decode("ascii")


def validate_matting_model(model):
    if model not in WEIGHTS:
        raise HTTPException(400, "不支持的人像模型")
    if not Path(WEIGHTS[model]).is_file():
        raise HTTPException(400, "所选人像模型未安装")


def require_portrait_size(image):
    if min(image.shape[:2]) < 64:
        raise HTTPException(400, "照片尺寸过小，请选择清晰照片")


async def require_safe_watermark_text(request: Request, text: str):
    """Check user-provided watermark text before it is rendered into a photo."""
    try:
        if not content_security_enabled():
            return
    except RuntimeError as exc:
        raise HTTPException(503, '文本内容安全检测服务暂不可用，请稍后重试') from exc

    token_subject = getattr(request.state, 'subject', None)
    if not token_subject:
        raise HTTPException(401, '请先登录后使用文字水印')
    subject = await asyncio.to_thread(resolve_subject, token_subject)
    openid = await asyncio.to_thread(get_openid, subject)
    result = await check_text(text, openid, scene=2, subject=subject)
    if result.get('available') is not True:
        raise HTTPException(503, '文本内容安全检测服务暂不可用，请稍后重试')
    if result.get('safe') is not True:
        raise HTTPException(400, '水印文字未通过内容安全检测，请修改后重试')


class ContentTextRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2500)
    scene: int = Field(default=2, ge=1, le=4)
    title: str = Field(default='', max_length=100)


class ContentMediaRequest(BaseModel):
    media_url: str = Field(min_length=10, max_length=2048)
    media_type: int = Field(default=2, ge=1, le=2)
    scene: int = Field(default=4, ge=1, le=4)


app.add_middleware(SecurityMiddleware)
app.add_middleware(ServiceObservationMiddleware)
app.post("/auth/wechat")(wechat_login)
app.include_router(membership_router)
app.include_router(payment_router)
app.include_router(status_router)

@app.get("/health")
def health():
    return {"status": "ok"}


# A fixed, non-user image gives the reviewer a safe public URL for the
# media_check_async example. It contains no uploaded content and is never
# written to the membership or photo data directories.
CONTENT_SECURITY_DEMO_MEDIA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@app.get("/content-security/demo-media", include_in_schema=False)
def content_security_demo_media():
    return Response(
        content=CONTENT_SECURITY_DEMO_MEDIA,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.post("/content-security/image")
async def content_security_image(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
):
    """Visible verification endpoint used by the audit/review flow.

    The same check is performed automatically by every image-processing route;
    this endpoint only exposes the metadata needed for a review recording.
    """
    return await audit_image(input_image, input_image_base64, cv2.IMREAD_UNCHANGED)


@app.post("/content-security/text")
async def content_security_text(request: Request, data: ContentTextRequest):
    subject = await asyncio.to_thread(resolve_subject, request.state.subject)
    openid = await asyncio.to_thread(get_openid, subject)
    result = await check_text(
        data.content, openid, scene=data.scene,
        title=data.title, subject=subject,
    )
    if result.get('available') is not True:
        raise HTTPException(503, '文本内容安全检测服务暂不可用，请稍后重试')
    if result.get('safe') is not True:
        raise HTTPException(400, '文本未通过内容安全检测，请修改后重试')
    return result


@app.post("/content-security/media")
async def content_security_media(request: Request, data: ContentMediaRequest):
    subject = await asyncio.to_thread(resolve_subject, request.state.subject)
    openid = await asyncio.to_thread(get_openid, subject)
    result = await check_media(
        data.media_url, openid, media_type=data.media_type,
        scene=data.scene, subject=subject,
    )
    if result.get('available') is not True:
        raise HTTPException(503, '媒体内容安全检测服务暂不可用，请稍后重试')
    if result.get('accepted') is not True:
        raise HTTPException(502, '微信未接受媒体内容安全检测任务，请稍后重试')
    return result


# 添加 CORS 中间件 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的请求来源
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=[
        "*"
    ],  # 允许的请求方法，例如：GET, POST 等，也可以指定 ["GET", "POST"]
    allow_headers=["*"],  # 允许的请求头，也可以指定具体的头部
)


# 证件照智能制作接口
@app.post("/idphoto")
async def idphoto_inference(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    height: int = Form(413, ge=1, le=2000),
    width: int = Form(295, ge=1, le=2000),
    human_matting_model: str = Form("birefnet-v1-lite"),
    face_detect_model: str = Form("mtcnn"),
    hd: bool = Form(True),
    dpi: int = Form(300, ge=72, le=600),
    face_align: bool = Form(False),
    horizontal_flip: bool = Form(False),
    whitening_strength: int = Form(0, ge=0, le=15),
    head_measure_ratio: float = Form(0.2),
    head_height_ratio: float = Form(0.45),
    top_distance_max: float = Form(0.12),
    top_distance_min: float = Form(0.10),
    brightness_strength: float = Form(0),
    contrast_strength: float = Form(0),
    sharpen_strength: float = Form(0),
    saturation_strength: float = Form(0),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    require_portrait_size(img)
    validate_matting_model(human_matting_model)

    # 将字符串转为元组
    size = (int(height), int(width))
    try:
        result = await asyncio.to_thread(
            run_creator, img, matting_model=human_matting_model, face_model=face_detect_model,
            size=size,
            head_measure_ratio=head_measure_ratio,
            head_height_ratio=head_height_ratio,
            head_top_range=(top_distance_max, top_distance_min),
            face_alignment=face_align,
            horizontal_flip=horizontal_flip,
            whitening_strength=whitening_strength,
            brightness_strength=brightness_strength,
            contrast_strength=contrast_strength,
            sharpen_strength=sharpen_strength,
            saturation_strength=saturation_strength,
        )
    except FaceError:
        result_message = {"status": False}
    # 如果检测到人脸数量等于1, 则返回标准证和高清照结果（png 4通道图像）
    else:
        result_image_standard_bytes = save_image_dpi_to_bytes(result.standard, None, dpi)

        result_message = {
            "status": True,
            "image_base64_standard": image_data_url(result_image_standard_bytes),
        }

        # 如果hd为True, 则增加高清照结果（png 4通道图像）
        if hd:
            result_image_hd_bytes = save_image_dpi_to_bytes(result.hd, None, dpi)
            result_message["image_base64_hd"] = image_data_url(result_image_hd_bytes)

    return result_message



# 格式转换：PNG 保留透明度；JPEG 将透明区域合成白色。
@app.post("/convert_image")
async def convert_image(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    output_format: str = Form("jpg"),
    target_kb: int = Form(0, ge=0, le=10240),
):
    if output_format not in ("jpg", "png"):
        raise HTTPException(400, "仅支持转换为 JPG 或 PNG")
    source = await read_image(input_image, input_image_base64, cv2.IMREAD_UNCHANGED)
    if source.dtype == np.uint16:
        source = (source / 257).astype(np.uint8)
    if source.ndim == 2:
        img = Image.fromarray(source)
    elif source.shape[2] == 4:
        img = Image.fromarray(cv2.cvtColor(source, cv2.COLOR_BGRA2RGBA))
    else:
        img = Image.fromarray(cv2.cvtColor(source, cv2.COLOR_BGR2RGB))
    if output_format == "jpg":
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, 'white')
            background.paste(img, mask=img.getchannel('A'))
            img = background
        else:
            img = img.convert('RGB')
        def jpeg_bytes(quality):
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
        if target_kb:
            low, high = 20, 95
            result = jpeg_bytes(low)
            while low <= high:
                quality = (low + high) // 2
                candidate = jpeg_bytes(quality)
                if len(candidate) <= target_kb * 1024:
                    result = candidate
                    low = quality + 1
                else:
                    high = quality - 1
        else:
            result = jpeg_bytes(90)
        mime = 'image/jpeg'
    else:
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        result = buffer.getvalue()
        mime = 'image/png'
    if len(result) > 20 * 1024 * 1024:
        raise HTTPException(413, '转换结果超过20MB，请使用较小的图片')
    return {
        'image_base64': f'data:{mime};base64,' + base64.b64encode(result).decode('ascii'),
        'size_bytes': len(result), 'width': img.width, 'height': img.height,
        'target_met': not target_kb or len(result) <= target_kb * 1024,
    }


# 人像抠图接口
@app.post("/human_matting")
async def human_matting_inference(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    human_matting_model: str = Form("birefnet-v1-lite"),
    dpi: int = Form(300, ge=72, le=600),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_COLOR)

    require_portrait_size(img)
    validate_matting_model(human_matting_model)

    try:
        result = await asyncio.to_thread(
            run_creator, img, matting_model=human_matting_model, change_bg_only=True,
        )
    except FaceError:
        result_message = {"status": False}

    else:
        result_image_standard_bytes = save_image_dpi_to_bytes(cv2.cvtColor(result.standard, cv2.COLOR_RGBA2BGRA), None, dpi)
        result_message = {
            "status": True,
            "image_base64": image_data_url(result_image_standard_bytes),
        }
    return result_message


# 透明图像添加纯色背景接口
@app.post("/add_background")
async def photo_add_background(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    color: str = Form("000000"),
    kb: int = Form(None, ge=1, le=10000),
    dpi: int = Form(300, ge=72, le=600),
    render: int = Form(0, ge=0, le=2),
):
    render_choice = ["pure_color", "updown_gradient", "center_gradient"]
    if len(color) != 6 or any(c not in '0123456789abcdefABCDEF' for c in color):
        raise HTTPException(400, '背景颜色无效')

    img = await read_image(input_image, input_image_base64, cv2.IMREAD_UNCHANGED)

    if len(img.shape) != 3 or img.shape[2] != 4:
        raise HTTPException(400, "请使用透明底图片换背景")

    color = hex_to_rgb(color)
    color = (color[2], color[1], color[0])

    result_image = add_background(
        img,
        bgr=color,
        mode=render_choice[render],
    ).astype(np.uint8)

    result_image = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
    if kb:
        result_image_bytes = resize_image_to_kb(result_image, None, int(kb), dpi=dpi)
    else:
        result_image_bytes = save_image_dpi_to_bytes(result_image, None, dpi=dpi)

    result_messgae = {
        "status": True,
        "image_base64": image_data_url(result_image_bytes),
    }

    return result_messgae


# 六寸排版照生成接口
@app.post("/generate_layout_photos")
async def generate_layout_photos(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    height: int = Form(413, ge=1, le=2000),
    width: int = Form(295, ge=1, le=2000),
    kb: int = Form(None, ge=1, le=10000),
    dpi: int = Form(300, ge=72, le=600),
    paper_size: str = Form("4r"),
    crop_line: bool = Form(False),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_COLOR)

    size = (int(height), int(width))

    papers = {"4r": (1795, 1205), "3r": (1500, 1051), "a4": (3508, 2479)}
    if paper_size not in papers:
        raise HTTPException(400, '不支持的相纸尺寸')
    # Paper dimensions are specified at 300 DPI. Input dimensions already
    # represent the selected specification at the supplied DPI.
    layout_width, layout_height = (round(value * dpi / 300) for value in papers[paper_size])
    typography_arr, typography_rotate = generate_layout_array(
        input_height=size[0], input_width=size[1],
        LAYOUT_WIDTH=layout_width, LAYOUT_HEIGHT=layout_height,
    )
    if not typography_arr:
        raise HTTPException(400, '所选照片尺寸无法放入相纸')

    result_layout_image = generate_layout_image(
        img, typography_arr, typography_rotate, height=size[0], width=size[1],
        crop_line=crop_line, LAYOUT_WIDTH=layout_width, LAYOUT_HEIGHT=layout_height,
    ).astype(np.uint8)

    result_layout_image = cv2.cvtColor(result_layout_image, cv2.COLOR_RGB2BGR)
    if kb:
        result_layout_image_bytes = resize_image_to_kb(
            result_layout_image, None, int(kb), dpi=dpi
        )
    else:
        result_layout_image_bytes = save_image_dpi_to_bytes(result_layout_image, None, dpi=dpi)

    result_layout_image_base64 = image_data_url(result_layout_image_bytes)

    result_messgae = {
        "status": True,
        "image_base64": result_layout_image_base64,
    }

    return result_messgae


# 透明图像添加水印接口
@app.post("/watermark")
async def watermark(
    request: Request,
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    text: str = Form("Hello"),
    size_query: Optional[int] = Query(None, alias="size", ge=1, le=200),
    size_form: Optional[int] = Form(None, alias="size", ge=1, le=200),
    opacity_query: Optional[float] = Query(None, alias="opacity", ge=0, le=1),
    opacity_form: Optional[float] = Form(None, alias="opacity", ge=0, le=1),
    angle_query: Optional[int] = Query(None, alias="angle", ge=0, le=360),
    angle_form: Optional[int] = Form(None, alias="angle", ge=0, le=360),
    color_query: Optional[str] = Query(None, alias="color"),
    color_form: Optional[str] = Form(None, alias="color"),
    space_query: Optional[int] = Query(None, alias="space", ge=1, le=500),
    space_form: Optional[int] = Form(None, alias="space", ge=1, le=500),
    kb: int = Form(None, ge=1, le=10000),
    dpi: int = Form(300, ge=72, le=600),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_COLOR)

    size = size_form if size_form is not None else (size_query if size_query is not None else 20)
    opacity = opacity_form if opacity_form is not None else (opacity_query if opacity_query is not None else 0.5)
    angle = angle_form if angle_form is not None else (angle_query if angle_query is not None else 30)
    color = color_form if color_form is not None else (color_query if color_query is not None else "#000000")
    space = space_form if space_form is not None else (space_query if space_query is not None else 25)
    if not text.strip() or len(text) > 100 or len(color) != 7 or not color.startswith('#') or any(c not in '0123456789abcdefABCDEF' for c in color[1:]):
        raise HTTPException(400, '水印文字或颜色无效')

    await require_safe_watermark_text(request, text)

    try:
        result_image = add_watermark(img, text, size, opacity, angle, color, space)

        result_image = cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR)
        if kb:
            result_image_bytes = resize_image_to_kb(result_image, None, int(kb), dpi=dpi)
        else:
            result_image_bytes = save_image_dpi_to_bytes(result_image, None, dpi=dpi)
        result_image_base64 = image_data_url(result_image_bytes)

        result_messgae = {
            "status": True,
            "image_base64": result_image_base64,
        }
    except Exception as exc:
        raise HTTPException(500, "图片处理失败，请稍后重试") from exc

    return result_messgae


# 设置照片KB值接口(RGB图)
@app.post("/set_kb")
async def set_kb(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    dpi: int = Form(300, ge=72, le=600),
    kb: int = Form(50, ge=1, le=10000),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_COLOR)

    try:
        result_image = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        result_image_bytes = resize_image_to_kb(result_image, None, int(kb), dpi=dpi)
        result_image_base64 = image_data_url(result_image_bytes)

        result_messgae = {
            "status": True,
            "image_base64": result_image_base64,
        }
    except Exception as exc:
        raise HTTPException(500, "图片处理失败，请稍后重试") from exc

    return result_messgae


# 证件照智能裁剪接口
@app.post("/idphoto_crop")
async def idphoto_crop_inference(
    input_image: UploadFile = File(None),
    input_image_base64: str = Form(None),
    height: int = Form(413, ge=1, le=2000),
    width: int = Form(295, ge=1, le=2000),
    face_detect_model: str = Form("mtcnn"),
    hd: bool = Form(True),
    dpi: int = Form(300, ge=72, le=600),
    head_measure_ratio: float = Form(0.2),
    head_height_ratio: float = Form(0.45),
    top_distance_max: float = Form(0.12),
    top_distance_min: float = Form(0.10),
):
    img = await read_image(input_image, input_image_base64, cv2.IMREAD_UNCHANGED)

    require_portrait_size(img)

    # 将字符串转为元组
    size = (int(height), int(width))
    try:
        result = await asyncio.to_thread(
            run_creator, img, face_model=face_detect_model,
            size=size,
            head_measure_ratio=head_measure_ratio,
            head_height_ratio=head_height_ratio,
            head_top_range=(top_distance_max, top_distance_min),
            crop_only=True,
        )
    except FaceError:
        result_message = {"status": False}
    # 如果检测到人脸数量等于1, 则返回标准证和高清照结果（png 4通道图像）
    else:
        result_image_standard_bytes = save_image_dpi_to_bytes(cv2.cvtColor(result.standard, cv2.COLOR_RGBA2BGRA), None, dpi)

        result_message = {
            "status": True,
            "image_base64_standard": image_data_url(result_image_standard_bytes),
        }

        # 如果hd为True, 则增加高清照结果（png 4通道图像）
        if hd:
            result_image_hd_bytes = save_image_dpi_to_bytes(cv2.cvtColor(result.hd, cv2.COLOR_RGBA2BGRA), None, dpi)
            result_message["image_base64_hd"] = image_data_url(result_image_hd_bytes)

    return result_message


if __name__ == "__main__":
    import uvicorn

    # 在8080端口运行推理服务
    uvicorn.run(app, host="127.0.0.1", port=8080)
