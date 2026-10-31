#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -f "$ROOT_DIR/.env.miniapp" ]; then . "$ROOT_DIR/.env.miniapp"; fi
for file in .env.miniapp .env.miniapp.payment; do
  [ -f "$ROOT_DIR/$file" ] || {
    printf '缺少 %s，请先运行 ./configure.sh\n' "$file" >&2
    exit 1
  }
done
[ -f "${IDPHOTO_DATA_DIR:-$ROOT_DIR/.miniapp_data}/admin.json" ] || {
  printf '%s\n' '缺少后台管理员密码，请先运行 ./configure.sh' >&2
  exit 1
}
for file in start_miniapp_api.sh start_miniapp_push.sh start_membership_admin.sh; do
  [ -x "$ROOT_DIR/hivision-overlay/$file" ] || {
    printf '缺少可执行启动脚本：%s\n' "$file" >&2
    exit 1
  }
done

LOG_DIR="$ROOT_DIR/.runtime/logs"
mkdir -p "$LOG_DIR"
PIDS=""
cleanup() {
  status=$?
  trap - EXIT INT TERM
  for pid in $PIDS; do kill "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  exit "$status"
}
trap cleanup EXIT INT TERM

"$ROOT_DIR/hivision-overlay/start_miniapp_api.sh" >"$LOG_DIR/api.log" 2>&1 & PIDS="$PIDS $!"
"$ROOT_DIR/hivision-overlay/start_miniapp_push.sh" >"$LOG_DIR/push.log" 2>&1 & PIDS="$PIDS $!"
"$ROOT_DIR/hivision-overlay/start_membership_admin.sh" >"$LOG_DIR/admin.log" 2>&1 & PIDS="$PIDS $!"

printf 'API、支付消息接收和会员后台已启动。日志目录：%s\n' "$LOG_DIR"
printf '按 Ctrl-C 可停止本次启动的服务。\n'
wait
