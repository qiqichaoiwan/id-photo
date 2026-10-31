"""Private, stable mapping between WeChat OpenIDs and internal user IDs."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException

from miniapp_membership import DATA_DIR, database


def identity_key():
    path = DATA_DIR / 'identity.key'
    DATA_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.exists():
        with database() as db:
            if db.execute('SELECT 1 FROM identity_users LIMIT 1').fetchone():
                raise RuntimeError('会员身份密钥缺失，请从备份恢复')
        temporary = DATA_DIR / ('.identity-' + secrets.token_hex(16))
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(secrets.token_bytes(32))
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Publish only a complete key when API and push start together.
                os.link(str(temporary), str(path))
            except FileExistsError:
                pass
        finally:
            temporary.unlink(missing_ok=True)
    raw = path.read_bytes()
    if len(raw) != 32:
        raise RuntimeError('会员身份密钥无效，请从备份恢复')
    return raw


def digest_openid(openid):
    return hmac.new(identity_key(), b'openid:' + openid.encode(), hashlib.sha256).hexdigest()


def encrypt_openid(openid):
    nonce = secrets.token_bytes(12)
    return nonce + AESGCM(identity_key()).encrypt(nonce, openid.encode(), b'idphoto-openid-v1')


def decrypt_openid(value):
    try:
        raw = bytes(value)
        return AESGCM(identity_key()).decrypt(raw[:12], raw[12:], b'idphoto-openid-v1').decode()
    except Exception:
        raise HTTPException(503, '会员身份信息暂不可用')


def bind_identity(openid, token_subject):
    digest = digest_openid(openid)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        user = db.execute('SELECT user_id FROM identity_users WHERE openid_hash = ?', (digest,)).fetchone()
        if user:
            user_id = user['user_id']
        else:
            user_id = secrets.token_hex(32)
            db.execute('INSERT INTO identity_users (user_id, openid_hash, encrypted_openid, created_at) VALUES (?, ?, ?, ?)',
                       (user_id, digest, encrypt_openid(openid), datetime.now(timezone.utc).isoformat()))
        alias = db.execute('SELECT user_id FROM identity_aliases WHERE subject = ?', (token_subject,)).fetchone()
        if alias and alias['user_id'] != user_id:
            raise HTTPException(503, '会员身份映射异常')
        db.execute('INSERT OR IGNORE INTO identity_aliases (subject, user_id) VALUES (?, ?)', (token_subject, user_id))
        # Migrate the earlier HMAC-based subject on the user's next login.
        old = db.execute('SELECT expires_at FROM members WHERE subject = ?', (token_subject,)).fetchone()
        current = db.execute('SELECT expires_at FROM members WHERE subject = ?', (user_id,)).fetchone()
        if old and not current:
            db.execute('UPDATE members SET subject = ? WHERE subject = ?', (user_id, token_subject))
        elif old:
            if old['expires_at'] > current['expires_at']:
                db.execute('UPDATE members SET expires_at = ? WHERE subject = ?', (old['expires_at'], user_id))
            db.execute('DELETE FROM members WHERE subject = ?', (token_subject,))
        db.execute('UPDATE orders SET subject = ? WHERE subject = ?', (user_id, token_subject))
        return user_id


def resolve_subject(subject):
    with database() as db:
        row = db.execute('SELECT user_id FROM identity_aliases WHERE subject = ?', (subject,)).fetchone()
    return row['user_id'] if row else subject


def get_openid(user_id):
    with database() as db:
        row = db.execute('SELECT encrypted_openid FROM identity_users WHERE user_id = ?', (user_id,)).fetchone()
    if not row:
        raise HTTPException(401, '请重新登录后再购买')
    return decrypt_openid(row['encrypted_openid'])
