"""Isolated identity and admin reference checks; no real data or WeChat calls."""
import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI

DATA = tempfile.TemporaryDirectory(prefix='xiaoqi-profile-tests-')
os.environ['IDPHOTO_DATA_DIR'] = DATA.name
os.environ['IDPHOTO_AUTH_REQUIRED'] = 'true'
os.environ['IDPHOTO_TOKEN_SECRET'] = 'isolated-profile-test-secret-' + ('x' * 40)
os.environ['IDPHOTO_ADMIN_PORT'] = '8091'
os.environ.pop('IDPHOTO_ADMIN_PUBLIC_HOST', None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend' / 'hivision-overlay'))

import miniapp_membership as membership
import miniapp_admin as admin
from miniapp_identity import bind_identity
from miniapp_security import SecurityMiddleware, issue_token, subject_for_openid

membership.initialize()
salt = b'profile-test-salt'
password = 'isolated-test-password'
hash_value = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
admin.PASSWORD_FILE.write_text(json.dumps({'salt': base64.b64encode(salt).decode(), 'hash': base64.b64encode(hash_value).decode()}))
app = FastAPI()
app.add_middleware(SecurityMiddleware)
app.include_router(membership.router)


class ProfileIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with membership.database() as db:
            for table in ('orders', 'members', 'identity_aliases', 'identity_users'):
                db.execute('DELETE FROM ' + table)
        self.owner = bind_identity('test-owner', subject_for_openid('test-owner'))
        self.other = bind_identity('test-other', subject_for_openid('test-other'))
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test')
        self.admin = httpx.AsyncClient(transport=httpx.ASGITransport(app=admin.app, client=('127.0.0.1', 54321)), base_url='http://127.0.0.1:8091', auth=('admin', password))
        self.owner_headers = {'Authorization': 'Bearer ' + issue_token('test-owner')}
        self.other_headers = {'Authorization': 'Bearer ' + issue_token('test-other')}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.admin.aclose()

    async def test_reference_is_private_and_available_without_orders(self):
        self.assertEqual((await self.client.get('/membership/profile')).status_code, 401)
        owner = await self.client.get('/membership/profile', headers=self.owner_headers)
        other = await self.client.get('/membership/profile', headers=self.other_headers)
        self.assertEqual(owner.status_code, 200)
        self.assertEqual(owner.json(), {'user_ref': self.owner[:16]})
        self.assertEqual(owner.headers['cache-control'], 'private, no-store')
        self.assertEqual(other.json(), {'user_ref': self.other[:16]})
        self.assertNotEqual(owner.json(), other.json())
        # Extra query parameters cannot select another user's reference.
        requested_other = await self.client.get('/membership/profile', headers=self.owner_headers, params={'user_ref': self.other[:16]})
        self.assertEqual(requested_other.json(), owner.json())
        detail = await self.admin.get('/api/users/' + self.owner[:16])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['user_ref'], owner.json()['user_ref'])
        self.assertEqual(detail.json()['orders'], [])
        listing = await self.admin.get('/api/users', params={'search': self.owner[:16]})
        self.assertEqual([item['user_ref'] for item in listing.json()['users']], [self.owner[:16]])
        adjustment = await self.admin.post(
            '/api/users/' + self.owner[:16] + '/adjust',
            headers={'origin': 'http://127.0.0.1:8091', 'x-admin-request': '1'},
            json={'mode': 'extend', 'months': 1, 'expected_expires_at': None, 'reason': '隔离测试补发'},
        )
        self.assertEqual(adjustment.status_code, 200)
        self.assertIsNotNone(adjustment.json()['expires_at'])
        self.assertIsNone((await self.admin.get('/api/users/' + self.other[:16])).json()['expires_at'])
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM orders').fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM admin_audit WHERE action='adjust_member'").fetchone()[0], 1)
        stale = await self.client.get('/membership/profile', headers={'Authorization': 'Bearer ' + issue_token('unbound')})
        self.assertEqual(stale.status_code, 401)

    async def test_order_reference_and_collision_fail_closed(self):
        now = datetime.now(timezone.utc).isoformat()
        with membership.database() as db:
            db.execute("INSERT INTO orders(order_no,subject,plan_name,months,price_fen,status,created_at,updated_at) VALUES ('test-order', ?, '测试会员', 1, 1200, 'paid', ?, ?)", (self.owner, now, now))
        order = await self.admin.get('/api/orders/test-order')
        self.assertEqual(order.status_code, 200)
        self.assertEqual(order.json()['order']['user_ref'], (await self.client.get('/membership/profile', headers=self.owner_headers)).json()['user_ref'])
        collision = self.owner[:16] + ('0' * 48 if self.owner[16:] != '0' * 48 else '1' * 48)
        with membership.database() as db:
            db.execute('INSERT INTO identity_users(user_id,openid_hash,encrypted_openid,created_at) VALUES (?, ?, ?, ?)', (collision, 'collision-digest', b'test', now))
        self.assertEqual((await self.client.get('/membership/profile', headers=self.owner_headers)).status_code, 503)
        self.assertEqual((await self.admin.get('/api/users/' + self.owner[:16])).status_code, 409)


if __name__ == '__main__':
    unittest.main()
