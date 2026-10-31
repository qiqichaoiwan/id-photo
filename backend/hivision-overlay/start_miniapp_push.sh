#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f .env.miniapp ] || [ ! -f .env.miniapp.payment ]; then
  printf '%s\n' '请先完成小程序及支付密钥配置' >&2
  exit 1
fi
. ./.env.miniapp
. ./.env.miniapp.payment
exec .venv/bin/python -m uvicorn miniapp_push:app --host 127.0.0.1 --port "${IDPHOTO_PUSH_PORT:-8092}" --no-access-log --no-proxy-headers
