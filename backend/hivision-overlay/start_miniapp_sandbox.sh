#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f .env.miniapp ] || [ ! -f .env.miniapp.payment ] || [ ! -f .env.miniapp.sandbox ]; then
  printf '%s\n' '请先完成小程序、支付及沙箱密钥配置' >&2
  exit 1
fi
. ./.env.miniapp
. ./.env.miniapp.payment
. ./.env.miniapp.sandbox
export IDPHOTO_AUTH_REQUIRED=true
exec .venv/bin/python -m uvicorn miniapp_sandbox:app --host 127.0.0.1 --port 8093 --no-access-log --no-proxy-headers
