#!/usr/bin/env python3
"""Create a private local configuration without putting secrets in shell history."""
import getpass
import os
import secrets
import shlex
from pathlib import Path

config_dir = Path(os.environ.get('IDPHOTO_CONFIG_DIR', Path(__file__).resolve().parent))
path = config_dir / '.env.miniapp'
if path.exists():
    raise SystemExit('配置文件已存在，请手动编辑，不会覆盖原文件。')
secret = getpass.getpass('请输入微信小程序 AppSecret（输入时不显示）：').strip()
if not 16 <= len(secret) <= 128 or not all(c.isascii() and (c.isalnum() or c in '_-') for c in secret):
    raise SystemExit('AppSecret 格式无效，请核对后重试。')
config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
contents = ('export WECHAT_APP_ID=wx7db67e2346adbeca\n'
            f'export WECHAT_APP_SECRET={secret}\n'
            f'export IDPHOTO_TOKEN_SECRET={secrets.token_urlsafe(48)}\n'
            'export IDPHOTO_AUTH_REQUIRED=true\n'
            'export IDPHOTO_CONTENT_SECURITY_ENABLED=true\n'
            f'export IDPHOTO_DATA_DIR={shlex.quote(os.environ.get("IDPHOTO_DATA_DIR", str(config_dir / ".miniapp_data")))}\n'
            '# Enable only when port 8080 is reachable solely by a trusted local Cloudflare Tunnel.\n'
            'export IDPHOTO_TRUST_CLOUDFLARE=true\n')
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as file:
    file.write(contents)
print('本地配置已保存，权限为 600；请勿分享或提交此文件。')
