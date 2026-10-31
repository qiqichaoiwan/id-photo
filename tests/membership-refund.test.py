"""Isolated membership/refund API checks. Never connects to WeChat or production data."""
import asyncio
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

DATA = tempfile.TemporaryDirectory(prefix='xiaoqi-refund-tests-')
os.environ['IDPHOTO_DATA_DIR'] = DATA.name
os.environ['IDPHOTO_AUTH_REQUIRED'] = 'true'
os.environ['IDPHOTO_TOKEN_SECRET'] = 'isolated-test-secret-' + ('x' * 40)
os.environ['IDPHOTO_ADMIN_PORT'] = '8091'
os.environ.pop('IDPHOTO_ADMIN_PUBLIC_HOST', None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend' / 'hivision-overlay'))

import miniapp_membership as membership
import miniapp_admin as admin
from miniapp_security import SecurityMiddleware, issue_token, subject_for_openid

membership.initialize()
salt = b'test-only-salt-16'
password = 'isolated-test-password'
hash_value = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
admin.PASSWORD_FILE.write_text(json.dumps({'salt': base64.b64encode(salt).decode(), 'hash': base64.b64encode(hash_value).decode()}))

app = FastAPI()
app.add_middleware(SecurityMiddleware)
app.include_router(membership.router)


class RefundIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with membership.database() as db:
            for table in ('refund_requests', 'payment_events', 'membership_grants', 'orders', 'members', 'admin_audit'):
                db.execute('DELETE FROM ' + table)
            self.owner = subject_for_openid('test-buyer')
            self.other = subject_for_openid('test-other')
            now = datetime.now(timezone.utc).isoformat()
            db.execute("INSERT INTO orders(order_no,subject,plan_name,months,price_fen,status,created_at,updated_at) VALUES ('test-paid', ?, '测试会员', 1, 1200, 'paid', ?, ?)", (self.owner, now, now))
            db.execute("INSERT INTO orders(order_no,subject,plan_name,months,price_fen,status,created_at,updated_at) VALUES ('test-pending', ?, '测试会员', 1, 1200, 'pending', ?, ?)", (self.owner, now, now))
            db.execute('INSERT INTO members(subject,expires_at) VALUES (?, ?)', (self.owner, '2030-01-01T00:00:00+00:00'))
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test')
        self.admin = httpx.AsyncClient(transport=httpx.ASGITransport(app=admin.app, client=('127.0.0.1', 54321)), base_url='http://127.0.0.1:8091', auth=('admin', password))
        self.owner_headers = {'Authorization': 'Bearer ' + issue_token('test-buyer')}
        self.other_headers = {'Authorization': 'Bearer ' + issue_token('test-other')}
        self.admin_headers = {'origin': 'http://127.0.0.1:8091', 'x-admin-request': '1'}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.admin.aclose()

    async def test_authorization_validation_and_duplicate_requests(self):
        path = '/membership/orders/test-paid/refund-requests'
        self.assertEqual((await self.client.post(path, json={'reason': '需要退款'})).status_code, 401)
        self.assertEqual((await self.client.post(path, headers=self.other_headers, json={'reason': '需要退款'})).status_code, 404)
        self.assertEqual((await self.client.get('/membership/orders/test-paid', headers=self.other_headers)).status_code, 404)
        self.assertEqual((await self.client.post('/membership/orders/test-pending/refund-requests', headers=self.owner_headers, json={'reason': '需要退款'})).status_code, 409)
        for reason in (' ', 'x', '字' * 201):
            self.assertEqual((await self.client.post(path, headers=self.owner_headers, json={'reason': reason})).status_code, 422)
        replies = await asyncio.gather(*(self.client.post(path, headers=self.owner_headers, json={'reason': '测试申请'}) for _ in range(6)))
        self.assertTrue(all(response.status_code == 200 for response in replies))
        self.assertEqual(len({response.json()['created_at'] for response in replies}), 1)
        detail = await self.client.get('/membership/orders/test-paid', headers=self.owner_headers)
        self.assertEqual(detail.json()['refund_request']['status'], 'submitted')
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM refund_requests').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT status FROM orders WHERE order_no = ?', ('test-paid',)).fetchone()[0], 'paid')
            self.assertEqual(db.execute('SELECT expires_at FROM members WHERE subject = ?', (self.owner,)).fetchone()[0], '2030-01-01T00:00:00+00:00')

    async def test_admin_workflow_does_not_refund_or_change_entitlement(self):
        await self.client.post('/membership/orders/test-paid/refund-requests', headers=self.owner_headers, json={'reason': '测试原因'})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=admin.app, client=('127.0.0.1', 54322)), base_url='http://127.0.0.1:8091') as anonymous:
            self.assertEqual((await anonymous.get('/api/refund-requests')).status_code, 401)
        listing = await self.admin.get('/api/refund-requests?state=pending')
        self.assertEqual(listing.status_code, 200)
        request_id = listing.json()['requests'][0]['id']
        endpoint = f'/api/refund-requests/{request_id}/update'
        bad_origin = await self.admin.post(endpoint, headers={'origin': 'https://wrong.example', 'x-admin-request': '1'}, json={'status': 'processing', 'note': '记录'})
        self.assertEqual(bad_origin.status_code, 403)
        missing_response = await self.admin.post(endpoint, headers=self.admin_headers, json={'status': 'closed', 'note': '已核实'})
        self.assertEqual(missing_response.status_code, 400)
        update = await self.admin.post(endpoint, headers=self.admin_headers, json={'status': 'processing', 'response': '正在核实', 'note': '内部记录'})
        self.assertEqual(update.status_code, 200)
        detail = (await self.client.get('/membership/orders/test-paid', headers=self.owner_headers)).json()['refund_request']
        self.assertEqual(detail['status'], 'processing')
        self.assertEqual(detail['response'], '正在核实')
        self.assertNotIn('admin_note', detail)
        closed = await self.admin.post(endpoint, headers=self.admin_headers, json={'status': 'closed', 'response': '请查看平台退款结果', 'note': '已核查'})
        self.assertEqual(closed.status_code, 200)
        self.assertEqual((await self.admin.post(endpoint, headers=self.admin_headers, json={'status': 'processing', 'note': '重复处理'})).status_code, 409)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT status FROM orders WHERE order_no=?', ('test-paid',)).fetchone()[0], 'paid')
            self.assertEqual(db.execute('SELECT expires_at FROM members WHERE subject=?', (self.owner,)).fetchone()[0], '2030-01-01T00:00:00+00:00')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM admin_audit WHERE action='update_refund_request'").fetchone()[0], 2)
        self.assertEqual((await self.client.post('/membership/orders/test-paid/refund-requests', headers=self.owner_headers, json={'reason': '再次咨询'})).status_code, 200)

    async def test_successful_platform_refund_cannot_be_requested_again(self):
        with membership.database() as db:
            db.execute("INSERT INTO payment_events(event_key,order_no,event_type,state,created_at) VALUES ('test', 'test-paid', 'xpay_refund_notify', 'manual_review', ?)", (datetime.now(timezone.utc).isoformat(),))
        result = await self.client.post('/membership/orders/test-paid/refund-requests', headers=self.owner_headers, json={'reason': '测试原因'})
        self.assertEqual(result.status_code, 409)


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        DATA.cleanup()
