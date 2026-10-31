"""Isolated refund entitlement checks; no production data or WeChat calls."""
import concurrent.futures
import base64
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

DATA = tempfile.TemporaryDirectory(prefix='xiaoqi-refund-entitlement-')
os.environ['IDPHOTO_DATA_DIR'] = DATA.name
os.environ['IDPHOTO_PAYMENT_ENV'] = '0'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend' / 'hivision-overlay'))

import miniapp_membership as membership
import miniapp_payment as payment
import miniapp_refund_entitlements as entitlements

membership.initialize()


class RefundEntitlementTests(unittest.TestCase):
    def setUp(self):
        with membership.database() as db:
            for table in ('membership_refund_revocations', 'refund_entitlement_checks', 'refund_transactions',
                          'refund_requests', 'payment_events', 'membership_grants', 'orders', 'members',
                          'admin_audit', 'member_adjustments'):
                db.execute('DELETE FROM ' + table)
        self.subject = 'test-user'
        self.remote_status = 8
        self.remote_left = 0
        self.remote_refund_fee = None
        self.remote_order_type = 0
        self.mockers = [patch('miniapp_refund_entitlements._query_refund', side_effect=self.refund_order),
                        patch('miniapp_refund._query_payment_order', side_effect=self.payment_order)]
        for mocker in self.mockers:
            mocker.start()

    def tearDown(self):
        for mocker in reversed(self.mockers):
            mocker.stop()

    def grant(self, name, when, months=1, price=1200):
        when = when.astimezone(timezone.utc)
        with membership.database() as db:
            current = db.execute('SELECT expires_at FROM members WHERE subject=?', (self.subject,)).fetchone()
            previous = entitlements._time(current['expires_at']) if current else when
            start = max(when, previous)
            expiry = payment.plus_calendar_months(start, months)
            db.execute('''INSERT INTO orders(order_no,subject,plan_name,months,price_fen,status,created_at,updated_at,
                product_id,platform_order_id,expires_at) VALUES (?,?,?,?,?,'paid',?,?,?,?,?)''',
                (name, self.subject, '测试会员', months, price, when.isoformat(), when.isoformat(),
                 'test-product', 'wx-' + name, expiry.isoformat()))
            db.execute('INSERT INTO membership_grants(order_no,subject,start_at,expires_at,created_at) VALUES (?,?,?,?,?)',
                       (name, self.subject, start.isoformat(), expiry.isoformat(), when.isoformat()))
            db.execute('INSERT INTO members(subject,expires_at) VALUES (?,?) ON CONFLICT(subject) DO UPDATE SET expires_at=excluded.expires_at',
                       (self.subject, expiry.isoformat()))
        return expiry

    def queue(self, order='A', amount=1200, number='R-refund'):
        with membership.database() as db:
            return entitlements.enqueue_check(db, order, number, 'wx-refund', amount, 'wx-' + order, 'notice')

    def refund_order(self, check, subject):
        return {'order_id':check['mch_refund_id'], 'wx_order_id':'wx-refund',
                'order_type':8 if self.remote_order_type == 7 else 1, 'env_type':1,
                'refund_fee':self.remote_refund_fee if self.remote_refund_fee is not None else check['amount_fen'],
                'status':self.remote_status}

    def payment_order(self, order):
        return {'order_id':order['order_no'], 'wx_order_id':'wx-' + order['order_no'],
                'order_type':self.remote_order_type, 'env_type':1, 'status':5 if self.remote_left == 0 else 4,
                'order_fee':order['price_fen'], 'paid_fee':order['price_fen'], 'left_fee':self.remote_left}

    def state(self, key):
        with membership.database() as db:
            return db.execute('SELECT state FROM refund_entitlement_checks WHERE check_key=?', (key,)).fetchone()[0]

    def expiry(self):
        with membership.database() as db:
            return entitlements._time(db.execute('SELECT expires_at FROM members WHERE subject=?', (self.subject,)).fetchone()[0])

    def test_full_refund_revokes_once_even_with_concurrent_retries(self):
        old = self.grant('A', datetime.now(timezone.utc) - timedelta(days=5))
        key = self.queue()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(entitlements.process_check, [key] * 4))
        self.assertEqual(self.state(key), 'revoked')
        self.assertLessEqual(self.expiry(), datetime.now(timezone.utc))
        self.assertLess(self.expiry(), old)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM membership_refund_revocations').fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM member_adjustments WHERE source='refund_auto'").fetchone()[0], 1)
        payment.grant_order('A')
        self.assertLessEqual(self.expiry(), datetime.now(timezone.utc))

    def test_other_renewal_is_recalculated_by_natural_month(self):
        self.grant('A', datetime(2027, 1, 31, 4, tzinfo=timezone.utc))
        self.grant('B', datetime(2027, 2, 1, 4, tzinfo=timezone.utc))
        key = self.queue()
        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 2, 2, 4, tzinfo=timezone.utc)
        with patch.object(entitlements, 'datetime', FixedDatetime):
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'revoked')
        self.assertEqual(self.expiry(), datetime(2027, 3, 2, 4, tzinfo=timezone.utc))

    def test_refunding_second_order_preserves_first_order(self):
        first = self.grant('A', datetime(2027, 1, 31, 4, tzinfo=timezone.utc))
        self.grant('B', datetime(2027, 2, 1, 4, tzinfo=timezone.utc))
        key = self.queue('B', number='R-second')
        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 2, 2, 4, tzinfo=timezone.utc)
        with patch.object(entitlements, 'datetime', FixedDatetime):
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'revoked')
        self.assertEqual(self.expiry(), first)

    def test_already_consumed_refunded_period_does_not_reduce_other_order(self):
        self.grant('A', datetime(2027, 1, 1, 4, tzinfo=timezone.utc))
        other_expiry = self.grant('B', datetime(2027, 1, 2, 4, tzinfo=timezone.utc))
        key = self.queue()
        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 2, 15, 4, tzinfo=timezone.utc)
        with patch.object(entitlements, 'datetime', FixedDatetime):
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'revoked')
        self.assertEqual(self.expiry(), other_expiry)

    def test_repeated_refunds_and_new_renewal_preserve_remaining_order(self):
        self.grant('A', datetime(2027, 1, 31, 4, tzinfo=timezone.utc))
        self.grant('B', datetime(2027, 2, 1, 4, tzinfo=timezone.utc))
        class FirstRefund(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 2, 2, 4, tzinfo=timezone.utc)
        with patch.object(entitlements, 'datetime', FirstRefund):
            entitlements.process_check(self.queue())
        self.grant('C', datetime(2027, 2, 3, 4, tzinfo=timezone.utc))
        class SecondRefund(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 2, 10, 4, tzinfo=timezone.utc)
        with patch.object(entitlements, 'datetime', SecondRefund):
            key = self.queue('B', number='R-second')
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'revoked')
        self.assertEqual(self.expiry(), datetime(2027, 3, 10, 4, tzinfo=timezone.utc))

    def test_partial_refund_leaves_membership_for_review(self):
        old = self.grant('A', datetime.now(timezone.utc))
        self.remote_left = 600
        key = self.queue(amount=600)
        entitlements.process_check(key)
        self.assertEqual(self.state(key), 'partial')
        self.assertEqual(self.expiry(), old)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT review_needed FROM orders WHERE order_no=?', ('A',)).fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM membership_refund_revocations').fetchone()[0], 0)

    def test_inconsistent_or_incomplete_refund_does_not_revoke(self):
        old = self.grant('A', datetime.now(timezone.utc))
        key = self.queue()
        self.remote_status = 4
        entitlements.process_check(key)
        self.assertEqual(self.state(key), 'pending')
        self.assertEqual(self.expiry(), old)
        self.remote_status = 8
        self.remote_refund_fee = 100
        entitlements.process_check(key)
        self.assertEqual(self.state(key), 'manual_review')
        self.assertEqual(self.expiry(), old)

    def test_missing_wechat_response_remains_pending(self):
        old = self.grant('A', datetime.now(timezone.utc))
        key = self.queue()
        with patch('miniapp_refund_entitlements._query_refund', side_effect=HTTPException(503)):
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'pending')
        self.assertEqual(self.expiry(), old)

    def test_payment_order_identity_mismatch_requires_review(self):
        old = self.grant('A', datetime.now(timezone.utc))
        key = self.queue()
        with patch('miniapp_refund._query_payment_order', side_effect=HTTPException(409)):
            entitlements.process_check(key)
        self.assertEqual(self.state(key), 'manual_review')
        self.assertEqual(self.expiry(), old)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT review_needed FROM orders WHERE order_no=?', ('A',)).fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM membership_refund_revocations').fetchone()[0], 0)

    def test_manual_adjustment_after_grant_requires_review(self):
        when = datetime.now(timezone.utc) - timedelta(days=2)
        old = self.grant('A', when)
        adjusted = old + timedelta(days=10)
        with membership.database() as db:
            db.execute('UPDATE members SET expires_at=? WHERE subject=?', (adjusted.isoformat(), self.subject))
            db.execute('''INSERT INTO member_adjustments(subject,previous_expires_at,new_expires_at,reason,source,created_at)
                VALUES (?,?,?,?,?,?)''', (self.subject, old.isoformat(), adjusted.isoformat(), '客服调整', 'admin', (when + timedelta(days=1)).isoformat()))
        key = self.queue()
        entitlements.process_check(key)
        self.assertEqual(self.state(key), 'manual_review')
        self.assertEqual(self.expiry(), adjusted)

    def test_signed_notice_must_match_buyer_order_and_amount(self):
        self.grant('A', datetime.now(timezone.utc))
        event = {'OpenId':'test-openid', 'Env':0, 'RetCode':0, 'RefundFee':1200,
                 'MchOrderId':'A', 'WxOrderId':'wx-A', 'MchRefundId':'R-refund', 'WxRefundId':'wx-refund'}
        with patch('miniapp_identity.get_openid', return_value='test-openid'):
            self.assertIsNone(entitlements.enqueue_notice({**event, 'OpenId':'other'}, 'A'))
            self.assertIsNone(entitlements.enqueue_notice({**event, 'MchOrderId':''}, 'A'))
            self.assertIsNone(entitlements.enqueue_notice({**event, 'WxOrderId':'wrong'}, 'A'))
            self.assertIsNone(entitlements.enqueue_notice({**event, 'RetCode':1}, 'A'))
            self.assertIsNotNone(entitlements.enqueue_notice(event, 'A'))

    def test_encrypted_callback_reconciles_full_refund_once(self):
        self.grant('A', datetime.now(timezone.utc) - timedelta(days=2))
        event = {'Event':'xpay_refund_notify', 'OpenId':'test-openid', 'Env':0, 'RetCode':0, 'RefundFee':1200,
                 'MchOrderId':'A', 'WxOrderId':'wx-A', 'MchRefundId':'R-refund', 'WxRefundId':'wx-refund'}
        env = {'WECHAT_APP_ID':'wx-isolated-test', 'WECHAT_PUSH_TOKEN':'isolated-token',
               'WECHAT_PUSH_AES_KEY':base64.b64encode(b'x'*32).decode().rstrip('=')}
        app = FastAPI()
        app.include_router(payment.router)
        with patch.dict(os.environ, env), patch('miniapp_identity.get_openid', return_value='test-openid'), \
             patch('miniapp_payment.get_openid', return_value='test-openid'):
            envelope = payment.encrypt_reply(event, '12345', 'nonce')
            params = {'timestamp':'12345', 'nonce':'nonce', 'encrypt_type':'aes',
                      'msg_signature':envelope['MsgSignature']}
            with TestClient(app) as client:
                for _ in range(2):
                    result = client.post('/payment/notify', params=params, json={'Encrypt':envelope['Encrypt']})
                    self.assertEqual(result.status_code, 200)
        with membership.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM membership_refund_revocations').fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT state FROM refund_entitlement_checks").fetchone()[0], 'revoked')
        self.assertLessEqual(self.expiry(), datetime.now(timezone.utc))

    def test_ios_refund_is_checked_before_revoking(self):
        self.grant('A', datetime.now(timezone.utc) - timedelta(days=2))
        self.remote_order_type = 7
        key = self.queue()
        entitlements.process_check(key)
        self.assertEqual(self.state(key), 'revoked')
        self.assertLessEqual(self.expiry(), datetime.now(timezone.utc))


if __name__ == '__main__':
    unittest.main()
