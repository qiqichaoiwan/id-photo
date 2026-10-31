#!/bin/sh
# 一键恢复“小七快照拍”本机服务和 Cloudflare Tunnel。
#
# 只重启已经配置好的 LaunchAgent，不修改密钥、会员数据库或 Tunnel 配置。
# 可通过 IDPHOTO_ROOT 覆盖线上后端目录；当前设备默认使用
# /Users/qiqi/HivisionIDPhotos。
set -u

IDPHOTO_ROOT=${IDPHOTO_ROOT:-/Users/qiqi/HivisionIDPhotos}
CLOUDFLARED_CONFIG=${CLOUDFLARED_CONFIG:-/Users/qiqi/.cloudflared/config.yml}
LAUNCH_AGENTS=${LAUNCH_AGENTS:-"$HOME/Library/LaunchAgents"}
USER_ID=$(id -u)
CHECK_ONLY=0
TIMEOUT_SECONDS=${IDPHOTO_RECOVERY_TIMEOUT:-30}

usage() {
  cat <<'EOF'
用法：recover_xiaoqi_photo.sh [--check]

默认：检查配置后，重启图片 API、支付推送、沙箱、会员后台及两个照片 Cloudflare Tunnel，最后检查本机和公网入口。
--check：只检查，不重启任何服务。

可选环境变量：
  IDPHOTO_ROOT             后端目录，默认 /Users/qiqi/HivisionIDPhotos
  CLOUDFLARED_CONFIG       Tunnel 配置文件
  IDPHOTO_RECOVERY_TIMEOUT 单个服务等待秒数，默认 30
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) CHECK_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf '未知参数：%s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

failures=0
info() { printf '[小七快照拍] %s\n' "$*"; }
warn() { printf '[小七快照拍][警告] %s\n' "$*" >&2; failures=$((failures + 1)); }

require_file() {
  if [ ! -f "$1" ]; then
    warn "缺少文件：${1}"
    return 1
  fi
  return 0
}

job_loaded() {
  launchctl print "gui/$USER_ID/$1" >/dev/null 2>&1
}

job_state() {
  launchctl print "gui/$USER_ID/$1" 2>/dev/null | awk -F'= ' '/job state =/{print $2; exit}'
}

ensure_job() {
  label=$1
  plist=$2
  if job_loaded "$label"; then
    return 0
  fi
  if [ -f "$plist" ]; then
    info "加载未注册的 LaunchAgent：${label}"
    if ! launchctl bootstrap "gui/$USER_ID" "$plist" >/dev/null 2>&1; then
      warn "无法加载 LaunchAgent：${label}"
      return 1
    fi
    return 0
  fi
  warn "找不到 LaunchAgent：${plist}"
  return 1
}

restart_job() {
  label=$1
  plist=$2
  ensure_job "$label" "$plist" || return 1
  if [ "$CHECK_ONLY" -eq 1 ]; then
    info "${label} 当前状态：$(job_state "$label" || true)"
    return 0
  fi
  info "重启：${label}"
  if ! launchctl kickstart -k "gui/$USER_ID/$label" >/dev/null 2>&1; then
    warn "重启命令失败：${label}"
    return 1
  fi
  elapsed=0
  while [ "$elapsed" -lt "$TIMEOUT_SECONDS" ]; do
    state=$(job_state "$label" || true)
    if [ "$state" = running ]; then
      info "$label 已运行"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  warn "${label} 未在 ${TIMEOUT_SECONDS} 秒内进入 running 状态（当前：${state:-unknown}）"
  return 1
}

http_status() {
  url=$1
  curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 3 --max-time 8 "$url" 2>/dev/null || printf '000'
}

check_http() {
  name=$1
  url=$2
  expected=$3
  actual=$(http_status "$url")
  if [ "$actual" = "$expected" ]; then
    info "${name}：HTTP ${actual}"
  else
    warn "${name}：HTTP ${actual}（预期 ${expected}）"
  fi
}

check_port() {
  name=$1
  port=$2
  if curl -sS -o /dev/null --connect-timeout 2 --max-time 4 "http://127.0.0.1:$port/" >/dev/null 2>&1; then
    info "${name}：127.0.0.1:${port} 可连接"
  else
    warn "${name}：127.0.0.1:${port} 不可连接"
  fi
}

info "开始恢复检查（目录：${IDPHOTO_ROOT}）"
preflight_ok=1
require_file "$CLOUDFLARED_CONFIG" || preflight_ok=0
require_file "$IDPHOTO_ROOT/.env.miniapp" || preflight_ok=0
require_file "$IDPHOTO_ROOT/.env.miniapp.payment" || preflight_ok=0
require_file "$IDPHOTO_ROOT/start_miniapp_api.sh" || preflight_ok=0
require_file "$IDPHOTO_ROOT/start_miniapp_push.sh" || preflight_ok=0
require_file "$IDPHOTO_ROOT/start_membership_admin.sh" || preflight_ok=0
if [ "$preflight_ok" -eq 0 ]; then
  printf '%s\n' '[小七快照拍] 基础文件不完整，已停止恢复，避免反复重启失败服务。' >&2
  exit 1
fi

if [ ! -f "$IDPHOTO_ROOT/.env.miniapp.admin" ]; then
  info '未找到 .env.miniapp.admin，继续使用本机后台访问；公网主机名由 Tunnel 配置单独控制'
fi

if [ -x "$(command -v cloudflared 2>/dev/null || true)" ]; then
  if cloudflared --config "$CLOUDFLARED_CONFIG" tunnel ingress validate >/dev/null 2>&1; then
    info 'Cloudflare Tunnel ingress 配置校验通过'
  else
    warn 'Cloudflare Tunnel ingress 配置校验失败；已跳过重启 Tunnel'
    tunnel_config_ok=0
  fi
else
  warn '找不到 cloudflared 命令；无法校验或恢复 Tunnel'
  tunnel_config_ok=0
fi
: "${tunnel_config_ok:=1}"

if [ "$CHECK_ONLY" -eq 0 ] && [ "$tunnel_config_ok" -eq 0 ]; then
  info '后端服务仍会继续恢复，但不会重启 Cloudflare Tunnel'
fi

restart_job com.hivision.api "$LAUNCH_AGENTS/com.hivision.api.plist"
restart_job com.qiqi.idphoto-payment-push "$LAUNCH_AGENTS/com.qiqi.idphoto-payment-push.plist"
restart_job com.qiqi.idphoto-membership-admin "$LAUNCH_AGENTS/com.qiqi.idphoto-membership-admin.plist"

if [ -f "$IDPHOTO_ROOT/.env.miniapp.sandbox" ] && [ -f "$IDPHOTO_ROOT/start_miniapp_sandbox.sh" ] && [ -f "$LAUNCH_AGENTS/com.qiqi.idphoto-payment-sandbox.plist" ]; then
  restart_job com.qiqi.idphoto-payment-sandbox "$LAUNCH_AGENTS/com.qiqi.idphoto-payment-sandbox.plist"
else
  info '未配置沙箱服务，跳过沙箱恢复（正式服务不受影响）'
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
  info '检查模式，不重启 Cloudflare Tunnel'
elif [ "$tunnel_config_ok" -eq 1 ]; then
  restart_job com.cloudflared.tunnel "$LAUNCH_AGENTS/com.cloudflared.tunnel.plist"
  restart_job com.jinxc.cloudflared-tunnel "$LAUNCH_AGENTS/com.jinxc.cloudflared-tunnel.plist"
fi

check_http '本机图片 API 健康检查' 'http://127.0.0.1:8080/health' 200
check_http '本机服务状态' 'http://127.0.0.1:8080/service-status' 200
check_port '支付推送服务' 8092
check_port '沙箱服务' 8093
check_http '会员后台认证入口' 'http://127.0.0.1:8091/' 401

check_http '公网图片 API' 'https://photo.ruize.eu.org/health' 200
check_http '公网服务状态' 'https://photo.ruize.eu.org/service-status' 200
admin_status=$(http_status 'https://idphoto-admin.ruize.eu.org/')
case "$admin_status" in
  200|302|403) info "公网管理后台：HTTP ${admin_status}（Access/后台认证正常）" ;;
  *) warn "公网管理后台：HTTP ${admin_status}（预期 200、302 或 403）" ;;
esac

if [ "$failures" -eq 0 ]; then
  info '恢复完成，所有检查通过。'
  exit 0
fi
printf '[小七快照拍] 恢复结束，但有 %s 项检查未通过；请查看上面的警告和服务日志。\n' "$failures" >&2
exit 1
