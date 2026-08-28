from urllib.parse import unquote, urlparse, parse_qs
import unittest

from flask import Flask
from flask.sessions import SecureCookieSessionInterface

from app.api.auth import jaccount_login
from app.core.config import get_settings
from app.services.portal_sso import decode_portal_identity


TEST_SECRET = "portal-test-secret"


def _signed_portal_cookie(payload: dict) -> str:
    portal = Flask("test-portal")
    portal.secret_key = TEST_SECRET
    serializer = SecureCookieSessionInterface().get_signing_serializer(portal)
    assert serializer is not None
    return serializer.dumps(payload)


class PortalSsoTest(unittest.TestCase):
    def test_decode_portal_identity_ignores_portal_admin_flag(self) -> None:
        settings = get_settings()
        original_secret = settings.portal_session_secret
        settings.portal_session_secret = TEST_SECRET
        try:
            cookie = _signed_portal_cookie(
                {"user": {"jaccount": "Student01", "name": "测试学生", "is_admin": True}}
            )
            self.assertEqual(
                decode_portal_identity(cookie),
                {"username": "student01", "displayName": "测试学生"},
            )
        finally:
            settings.portal_session_secret = original_secret

    def test_jaccount_login_builds_subpath_callback(self) -> None:
        settings = get_settings()
        originals = (
            settings.portal_session_secret,
            settings.app_base_path,
            settings.portal_login_url,
        )
        settings.portal_session_secret = TEST_SECRET
        settings.app_base_path = "/shengya"
        settings.portal_login_url = "https://ai4edu.sjtu.edu.cn/auth/jaccount/login"
        try:
            response = jaccount_login("/my-reports")
            self.assertEqual(response.status_code, 302)
            parsed = urlparse(response.headers["location"])
            self.assertEqual(parsed.path, "/auth/jaccount/login")
            portal_next = parse_qs(parsed.query)["next"][0]
            self.assertIn(
                "/shengya/api/auth/jaccount/callback",
                unquote(portal_next),
            )
            self.assertIn("%2Fshengya%2Fmy-reports", unquote(response.headers["location"]))
        finally:
            (
                settings.portal_session_secret,
                settings.app_base_path,
                settings.portal_login_url,
            ) = originals


if __name__ == "__main__":
    unittest.main()
