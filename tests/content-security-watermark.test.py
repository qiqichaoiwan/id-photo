"""Watermark moderation checks use mocked WeChat and disposable state only."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = tempfile.TemporaryDirectory(prefix='xiaoqi-watermark-security-')
os.environ['IDPHOTO_DATA_DIR'] = DATA.name
os.environ['IDPHOTO_AUTH_REQUIRED'] = 'true'
os.environ['IDPHOTO_TOKEN_SECRET'] = 'isolated-watermark-test-' + 'x' * 40
os.environ['IDPHOTO_CONTENT_SECURITY_ENABLED'] = 'true'
sys.path.insert(0, str(ROOT / 'backend' / 'hivision-core'))
sys.path.insert(0, str(ROOT / 'backend' / 'hivision-overlay'))

import deploy_api as api
import miniapp_content_security as security
from miniapp_security import issue_token


class WatermarkSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app), base_url='http://test')
        self.headers = {'Authorization': 'Bearer ' + issue_token('test-buyer')}
        self.image = np.zeros((4, 4, 3), dtype=np.uint8)
        self.patches = [
            patch.object(api, 'read_image', new=AsyncMock(return_value=self.image)),
            patch.object(api, 'resolve_subject', return_value='test-subject'),
            patch.object(api, 'get_openid', return_value='test-openid'),
            patch.object(api, 'add_watermark', return_value=self.image),
            patch.object(api, 'save_image_dpi_to_bytes', return_value=b'example-png'),
        ]
        self.mocks = [item.start() for item in self.patches]

    async def asyncTearDown(self):
        await self.client.aclose()
        for item in reversed(self.patches):
            item.stop()

    async def test_safe_text_is_checked_before_rendering(self):
        with patch.object(api, 'check_text', new=AsyncMock(return_value={'available': True, 'safe': True})) as check:
            response = await self.client.post('/watermark', headers=self.headers, data={'text': '测试水印'})
        self.assertEqual(response.status_code, 200)
        check.assert_awaited_once_with('测试水印', 'test-openid', scene=2, subject='test-subject')
        self.mocks[3].assert_called_once()

    async def test_risk_or_unavailable_check_never_renders(self):
        for result, code in (({'available': True, 'safe': False}, 400),
                             ({'available': False, 'safe': None}, 503)):
            with self.subTest(result=result):
                self.mocks[3].reset_mock()
                with patch.object(api, 'check_text', new=AsyncMock(return_value=result)):
                    response = await self.client.post('/watermark', headers=self.headers, data={'text': '测试水印'})
                self.assertEqual(response.status_code, code)
                self.mocks[3].assert_not_called()

    async def test_login_is_required(self):
        with patch.object(api, 'check_text', new=AsyncMock()) as check:
            response = await self.client.post('/watermark', data={'text': '测试水印'})
        self.assertEqual(response.status_code, 401)
        check.assert_not_awaited()
        self.mocks[3].assert_not_called()

    async def test_accepted_media_is_a_pending_check(self):
        with patch.object(security, '_audit') as audit:
            result = security._result(kind='media', payload={'errcode': 0}, available=True, safe=None)
        self.assertIsNone(result['safe'])
        self.assertEqual(audit.call_args.args[0]['state'], 'pending')


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        DATA.cleanup()
