#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OVERLAY_DIR="$ROOT_DIR/hivision-overlay"
export IDPHOTO_CONFIG_DIR="$ROOT_DIR"
export IDPHOTO_DATA_DIR="${IDPHOTO_DATA_DIR:-$ROOT_DIR/.miniapp_data}"
export PYTHONPATH="$OVERLAY_DIR:$ROOT_DIR/hivision-core${PYTHONPATH:+:$PYTHONPATH}"

PYTHON=${PYTHON_BIN:-"$ROOT_DIR/.venv/bin/python"}
if [ ! -x "$PYTHON" ]; then
  printf '%s\n' '请先运行 ./bootstrap.sh 准备 Python 环境。' >&2
  exit 1
fi

"$PYTHON" "$OVERLAY_DIR/setup_miniapp_secrets.py"
"$PYTHON" "$OVERLAY_DIR/setup_payment_secrets.py"
"$PYTHON" "$OVERLAY_DIR/setup_membership_admin.py"

printf '%s\n' '本机配置已生成。请在 .env.miniapp.admin 中填写后台公网主机名（如需公网后台），然后运行 ./start-all.sh。'
