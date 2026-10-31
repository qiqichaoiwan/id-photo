#!/bin/sh
set -eu
OVERLAY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$OVERLAY_DIR/.." && pwd)
CORE_DIR="$ROOT_DIR/hivision-core"
cd "$OVERLAY_DIR"
if [ ! -f "$ROOT_DIR/.env.miniapp" ] || [ ! -f "$ROOT_DIR/.env.miniapp.payment" ] || [ ! -f "$ROOT_DIR/.env.miniapp.sandbox" ]; then
  printf '%s\n' '请先完成小程序、支付及沙箱密钥配置' >&2
  exit 1
fi
. "$ROOT_DIR/.env.miniapp"
. "$ROOT_DIR/.env.miniapp.payment"
. "$ROOT_DIR/.env.miniapp.sandbox"
export IDPHOTO_AUTH_REQUIRED=true
export PYTHONPATH="$OVERLAY_DIR:$CORE_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "${IDPHOTO_VENV:-$ROOT_DIR/.venv}/bin/python" -m uvicorn miniapp_sandbox:app --host 127.0.0.1 --port 8093 --no-access-log --no-proxy-headers
