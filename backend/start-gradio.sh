#!/bin/sh
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON=${PYTHON_BIN:-"$ROOT_DIR/.venv/bin/python"}
[ -x "$PYTHON" ] || { printf '%s\n' '请先运行 ./bootstrap.sh。' >&2; exit 1; }
cd "$ROOT_DIR/hivision-core"
exec "$PYTHON" app.py --host "${HIVISION_HOST:-127.0.0.1}" --port "${HIVISION_GRADIO_PORT:-7860}"
