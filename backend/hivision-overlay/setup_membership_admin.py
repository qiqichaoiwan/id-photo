"""Set the local membership admin password without putting it in shell history."""
import base64
import getpass
import hashlib
import json
import os

from miniapp_membership import DATA_DIR


def main():
    password = getpass.getpass('设置管理员密码（至少 12 个字符）：')
    if len(password) < 12:
        raise SystemExit('密码长度不足，未保存。')
    if password != getpass.getpass('再次输入管理员密码：'):
        raise SystemExit('两次密码不一致，未保存。')
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = DATA_DIR / 'admin.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump({'salt': base64.b64encode(salt).decode('ascii'), 'hash': base64.b64encode(digest).decode('ascii')}, output)
    os.chmod(path, 0o600)
    print('管理员密码已配置。账号为 admin。')


if __name__ == '__main__':
    main()
