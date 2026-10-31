#!/bin/sh
set -eu
OVERLAY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$OVERLAY_DIR/.." && pwd)
CORE_DIR="$ROOT_DIR/hivision-core"
cd "$OVERLAY_DIR"
if [ ! -f "$ROOT_DIR/.env.miniapp" ]; then
  printf '%s\n' '缺少 .env.miniapp，请先运行 .venv/bin/python setup_miniapp_secrets.py' >&2
  exit 1
fi
# This file is generated locally by setup_miniapp_secrets.py and contains exports.
. "$ROOT_DIR/.env.miniapp"
if [ -f "$ROOT_DIR/.env.miniapp.payment" ]; then
  . "$ROOT_DIR/.env.miniapp.payment"
fi
export PYTHONPATH="$OVERLAY_DIR:$CORE_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "${IDPHOTO_VENV:-$ROOT_DIR/.venv}/bin/python" -m uvicorn deploy_api:app --host 127.0.0.1 --port "${IDPHOTO_PORT:-8080}" --no-access-log --no-proxy-headers
