#!/bin/sh
set -eu
OVERLAY_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$OVERLAY_DIR/.." && pwd)
CORE_DIR="$ROOT_DIR/hivision-core"
cd "$OVERLAY_DIR"
if [ -f "$ROOT_DIR/.env.miniapp" ]; then . "$ROOT_DIR/.env.miniapp"; fi
if [ -f "$ROOT_DIR/.env.miniapp.payment" ]; then . "$ROOT_DIR/.env.miniapp.payment"; fi
if [ -f "$ROOT_DIR/.env.miniapp.admin" ]; then . "$ROOT_DIR/.env.miniapp.admin"; fi
export PYTHONPATH="$OVERLAY_DIR:$CORE_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "${IDPHOTO_VENV:-$ROOT_DIR/.venv}/bin/python" "$OVERLAY_DIR/miniapp_admin.py"
