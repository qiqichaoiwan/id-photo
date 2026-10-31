"""Dedicated WeChat push process, isolated from CPU-heavy image processing."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from miniapp_identity import identity_key
from miniapp_membership import initialize
from miniapp_payment import decode_push_key, receive_push, required, verify_push


@asynccontextmanager
async def lifespan(app):
    required('WECHAT_APP_ID')
    required('WECHAT_PUSH_TOKEN')
    if len(decode_push_key()) != 32:
        raise RuntimeError('微信消息推送密钥无效')
    initialize()
    identity_key()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_api_route('/payment/notify', verify_push, methods=['GET'])
app.add_api_route('/payment/notify', receive_push, methods=['POST'])
