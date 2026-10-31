"""Store sandbox-only credentials and isolate its database from real members."""
import getpass
import os
import secrets
import shlex
from pathlib import Path

ROOT = Path(os.environ.get('IDPHOTO_CONFIG_DIR', Path(__file__).resolve().parent))
PATH = ROOT / '.env.miniapp.sandbox'


def main():
    if PATH.exists():
        raise SystemExit('沙箱配置已存在，未覆盖。')
    key = getpass.getpass('微信虚拟支付沙箱 AppKey（输入不显示）：').strip()
    if not key:
        raise SystemExit('未填写沙箱 AppKey，未保存。')
    settings = {
        'WECHAT_PAY_APP_KEY': key,
        'IDPHOTO_PAYMENT_ENV': '1',
        'IDPHOTO_PAYMENT_ENABLED': 'true',
        'IDPHOTO_TOKEN_SECRET': secrets.token_hex(32),
        'IDPHOTO_DATA_DIR': os.environ.get('IDPHOTO_SANDBOX_DATA_DIR', str(ROOT / '.miniapp_sandbox')),
    }
    fd = os.open(str(PATH), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out:
        for name, value in settings.items():
            out.write(f'export {name}={shlex.quote(value)}\n')
    print('沙箱配置已保存。正式支付开关和正式会员数据不受影响。')


if __name__ == '__main__':
    main()
