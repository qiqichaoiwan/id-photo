"""Refund initiation tests using disposable SQLite and mocked WeChat only."""
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
from unittest.mock import patch

import httpx
import requests

DATA = tempfile.TemporaryDirectory(prefix='xiaoqi-direct-refund-')
os.environ['IDPHOTO_DATA_DIR'] = DATA.name
os.environ['IDPHOTO_AUTH_REQUIRED'] = 'true'
os.environ['IDPHOTO_TOKEN_SECRET'] = 'isolated-refund-test-secret-' + 'x' * 40
os.environ['IDPHOTO_ADMIN_PORT'] = '8091'
os.environ['IDPHOTO_PAYMENT_ENV'] = '0'
os.environ.pop('IDPHOTO_ADMIN_PUBLIC_HOST', None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend' / 'hivision-overlay'))

import miniapp_membership as membership
import miniapp_admin as admin
import miniapp_payment as payment
from miniapp_identity import bind_identity
from miniapp_security import subject_for_openid

membership.initialize()
salt, password = b'direct-test-salt', 'isolated-test-password'
digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
admin.PASSWORD_FILE.write_text(json.dumps({'salt':base64.b64encode(salt).decode(), 'hash':base64.b64encode(digest).decode()}))


class FakeResponse:
    def __init__(self, data): self.data = data
    def raise_for_status(self): pass
    def json(self): return self.data


class DirectRefundTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        with membership.database() as db:
            for table in ('membership_refund_revocations', 'refund_entitlement_checks', 'refund_transactions', 'refund_requests', 'payment_events', 'membership_grants', 'orders', 'members', 'admin_audit', 'identity_aliases', 'identity_users'):
                db.execute('DELETE FROM ' + table)
        self.subject = bind_identity('buyer-openid', subject_for_openid('buyer-openid'))
        self.order_no = 'M' + '1' * 30
        now = datetime.now(timezone.utc).isoformat()
        with membership.database() as db:
            db.execute('''INSERT INTO orders(order_no,subject,plan_name,months,price_fen,status,created_at,updated_at,product_id,platform_order_id)
                VALUES (?,?,?,1,1200,'paid',?,?,?,?)''', (self.order_no, self.subject, '测试会员', now, now, 'test-product', 'wx-order'))
            db.execute('INSERT INTO members(subject,expires_at) VALUES (?,?)', (self.subject, '2030-01-01T00:00:00+00:00'))
        self.remote = {'order_id':self.order_no,'order_type':0,'env_type':1,'status':4,'order_fee':1200,'paid_fee':1200,'left_fee':1200,'wx_order_id':'wx-order'}
        self.calls = []
        self.refund_behavior = 'success'
        self.bad_refund_query = False
        self.mockers = [patch('miniapp_refund.wechat_access_token', return_value='test-token'),
                        patch('miniapp_refund.pay_sig', return_value='test-signature'),
                        patch('miniapp_refund.get_openid', return_value='buyer-openid'),
                        patch('miniapp_payment.get_openid', return_value='buyer-openid'),
                        patch('miniapp_refund.requests.post', side_effect=self.wechat)]
        for item in self.mockers: item.start()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=admin.app, client=('127.0.0.1', 12345)), base_url='http://127.0.0.1:8091', auth=('admin',password))
        self.headers = {'origin':'http://127.0.0.1:8091','x-admin-request':'1'}
        self.path = '/api/orders/' + self.order_no

    async def asyncTearDown(self):
        await self.client.aclose()
        for item in reversed(self.mockers): item.stop()

    def wechat(self, url, **kwargs):
        body = json.loads(kwargs['data'])
        self.calls.append((url, body, kwargs['params']))
        if url.endswith('/query_order'):
            if body.get('order_id', '').startswith('R'):
                return FakeResponse({'errcode':0,'order':{'order_id':body['order_id'],'wx_order_id':'wx-refund',
                    'order_type':1,'env_type':1,'status':8,'refund_fee':500 if self.bad_refund_query else 600}})
            return FakeResponse({'errcode':0,'order':dict(self.remote)})
        if url.endswith('/refund_order'):
            if self.refund_behavior == 'timeout': raise requests.Timeout()
            if self.refund_behavior == 'callback-first':
                payment.refund_event(self.notice(body['refund_order_id']))
            if self.refund_behavior == 'mismatch':
                return FakeResponse({'errcode':0,'refund_order_id':'wrong'})
            return FakeResponse({'errcode':0,'refund_order_id':body['refund_order_id'],
                                 'refund_wx_order_id':'wx-refund','pay_order_id':self.order_no,'pay_wx_order_id':'wx-order'})
        raise AssertionError('Unexpected WeChat URL')

    def notice(self, refund_id, **changes):
        event = {'Event':'xpay_refund_notify','OpenId':'buyer-openid','Env':0,'MchOrderId':self.order_no,
                 'WxOrderId':'wx-order','MchRefundId':refund_id,'WxRefundId':'wx-refund','RefundFee':600,'RetCode':0}
        event.update(changes)
        return event

    def payload(self, key='a'*32, amount=600, left=1200):
        return {'request_key':key,'amount_fen':amount,'expected_left_fen':left,'reason_code':'3','note':'客服工单测试'}

    def refund_calls(self): return [call for call in self.calls if call[0].endswith('/refund_order')]

    async def test_quote_submit_replay_and_notification(self):
        quote = await self.client.get(self.path + '/refund-quote')
        self.assertEqual((quote.status_code, quote.json()['left_fee']), (200, 1200))
        result = await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['state'], 'accepted')
        refund_id = result.json()['refund_id']
        sent = self.refund_calls()[0][1]
        self.assertEqual((sent['order_id'],sent['refund_order_id'],sent['left_fee'],sent['refund_fee'],sent['req_from'],sent['env']), (self.order_no,refund_id,1200,600,'1',0))
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())).json()['refund_id'], refund_id)
        self.assertEqual(len(self.refund_calls()), 1)
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload('b'*32))).status_code, 409)
        queried = await self.client.post('/api/refunds/' + refund_id + '/refresh', headers=self.headers)
        self.assertEqual((queried.status_code, queried.json()['query_status'], queried.json()['state']), (200, 8, 'accepted'))
        contradictory = await self.client.post('/api/refunds/' + refund_id + '/review', headers=self.headers, json={'outcome':'not_refunded','note':'测试矛盾结果'})
        self.assertEqual(contradictory.status_code, 409)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT review_needed FROM orders WHERE order_no=?',(self.order_no,)).fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT expires_at FROM members WHERE subject=?',(self.subject,)).fetchone()[0], '2030-01-01T00:00:00+00:00')
        self.bad_refund_query = True
        self.assertEqual((await self.client.post('/api/refunds/' + refund_id + '/refresh', headers=self.headers)).status_code, 503)
        payment.refund_event(self.notice(refund_id, RefundFee=500))
        detail = (await self.client.get(self.path)).json()
        self.assertEqual(detail['refunds'][0]['state'], 'accepted')
        payment.refund_event(self.notice(refund_id))
        payment.refund_event(self.notice(refund_id))
        detail = (await self.client.get(self.path)).json()
        self.assertEqual(detail['refunds'][0]['state'], 'notice_success')
        self.assertEqual(detail['order']['review_needed'], 1)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT expires_at FROM members WHERE subject=?',(self.subject,)).fetchone()[0], '2030-01-01T00:00:00+00:00')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM admin_audit WHERE action='start_refund'").fetchone()[0], 1)

    async def test_ios_and_changed_amount_are_blocked(self):
        self.remote['order_type'] = 7
        quote = await self.client.get(self.path + '/refund-quote')
        self.assertEqual((quote.json()['channel'],quote.json()['eligible']), ('ios',False))
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())).status_code, 409)
        self.assertEqual(len(self.refund_calls()), 0)
        self.remote.update(order_type=0,left_fee=900)
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())).status_code, 409)
        self.assertEqual(len(self.refund_calls()), 0)

    async def test_timeout_locks_until_manual_platform_review(self):
        self.refund_behavior = 'timeout'
        result = await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())
        self.assertEqual(result.json()['state'], 'unknown')
        refund_id = result.json()['refund_id']
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())).json()['refund_id'], refund_id)
        self.assertEqual((await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload('b'*32))).status_code, 409)
        self.assertEqual(len(self.refund_calls()), 1)
        review = await self.client.post('/api/refunds/' + refund_id + '/review', headers=self.headers, json={'outcome':'not_refunded','note':'微信后台核实未退款'})
        self.assertEqual((review.status_code, review.json()['state']), (200, 'not_refunded'))
        with membership.database() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM admin_audit WHERE action='review_refund'").fetchone()[0], 1)

    async def test_callback_before_response_is_not_overwritten(self):
        self.refund_behavior = 'callback-first'
        result = await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['state'], 'notice_success')

    async def test_malformed_response_and_admin_boundary(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=admin.app, client=('127.0.0.1', 12346)), base_url='http://127.0.0.1:8091') as anonymous:
            self.assertEqual((await anonymous.get(self.path + '/refund-quote')).status_code, 401)
        bad = await self.client.post(self.path + '/refund', headers={'origin':'https://wrong.example','x-admin-request':'1'}, json=self.payload())
        self.assertEqual(bad.status_code, 403)
        self.refund_behavior = 'mismatch'
        result = await self.client.post(self.path + '/refund', headers=self.headers, json=self.payload())
        self.assertEqual(result.json()['state'], 'unknown')
        self.assertEqual(len(self.refund_calls()), 1)

    async def test_parallel_requests_cannot_create_two_refunds(self):
        responses = await asyncio.gather(*(self.client.post(self.path + '/refund', headers=self.headers, json=self.payload(key)) for key in ('a'*32, 'b'*32)))
        self.assertEqual(sorted(response.status_code for response in responses), [200,409])
        self.assertEqual(len(self.refund_calls()), 1)


if __name__ == '__main__':
    unittest.main()
