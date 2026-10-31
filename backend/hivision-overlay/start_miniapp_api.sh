#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -f .env.miniapp ]; then
  printf '%s\n' '缺少 .env.miniapp，请先运行 .venv/bin/python setup_miniapp_secrets.py' >&2
  exit 1
fi
# This file is generated locally by setup_miniapp_secrets.py and contains exports.
. ./.env.miniapp
if [ -f .env.miniapp.payment ]; then
  . ./.env.miniapp.payment
fi
exec .venv/bin/python -m uvicorn deploy_api:app --host 127.0.0.1 --port "${IDPHOTO_PORT:-8080}" --no-access-log --no-proxy-headers
