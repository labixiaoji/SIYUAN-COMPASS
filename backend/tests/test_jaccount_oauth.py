import time
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import jwt
from starlette.requests import Request

from app.api.auth import jaccount_callback, jaccount_login
from app.core.config import get_settings
from app.services.auth import create_access_token, require_user
from app.services.jaccount_oauth import JAccountOAuthError, decode_identity_token


def _request_with_cookies(cookies: dict[str, str]) -> Request:
    cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "https",
            "path": "/api/auth/jaccount/callback",
            "query_string": b"",
            "headers": [(b"cookie", cookie_header.encode())],
            "client": ("127.0.0.1", 12345),
            "server": ("example.test", 443),
        }
    )


class JAccountOAuthTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = get_settings()
        self.settings_patch = patch.multiple(
            self.settings,
            jaccount_client_id="test-client",
            jaccount_client_secret="test-secret-at-least-32-bytes-long",
            jaccount_authorize_url="https://jaccount.sjtu.edu.cn/oauth2/authorize",
            jaccount_token_url="https://jaccount.sjtu.edu.cn/oauth2/token",
            jaccount_logout_url="https://jaccount.sjtu.edu.cn/oauth2/logout",
            jaccount_issuer="https://jaccount.sjtu.edu.cn/oauth2/",
            jaccount_redirect_uri="https://ai4edu.sjtu.edu.cn/shengya/api/auth/jaccount/callback",
            jaccount_scope="openid",
            jaccount_post_logout_redirect_uri="https://ai4edu.sjtu.edu.cn/shengya/",
            public_app_url="https://ai4edu.sjtu.edu.cn",
            app_base_path="/shengya",
            auth_secret="test-app-secret",
        )
        self.settings_patch.start()

    def tearDown(self) -> None:
        self.settings_patch.stop()

    def test_login_redirects_to_authorization_code_flow(self) -> None:
        response = jaccount_login("/my-reports")

        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.headers["location"])
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "jaccount.sjtu.edu.cn")
        self.assertEqual(parsed.path, "/oauth2/authorize")
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["openid"])
        self.assertEqual(query["client_id"], ["test-client"])
        self.assertEqual(
            query["redirect_uri"],
            ["https://ai4edu.sjtu.edu.cn/shengya/api/auth/jaccount/callback"],
        )
        self.assertTrue(query["state"][0])
        self.assertTrue(query["nonce"][0])
        self.assertGreaterEqual(len(response.headers.getlist("set-cookie")), 3)

    def test_identity_token_requires_matching_nonce(self) -> None:
        token = jwt.encode(
            {
                "iss": self.settings.jaccount_issuer,
                "sub": "Student01",
                "aud": self.settings.jaccount_client_id,
                "exp": int(time.time()) + 300,
                "iat": int(time.time()),
                "nonce": "expected-nonce",
                "name": "测试学生",
            },
            self.settings.jaccount_client_secret,
            algorithm="HS256",
        )

        identity = decode_identity_token(token, expected_nonce="expected-nonce")

        self.assertEqual(identity.username, "student01")
        self.assertEqual(identity.display_name, "测试学生")
        with self.assertRaises(JAccountOAuthError):
            decode_identity_token(token, expected_nonce="wrong-nonce")

    def test_compass_session_cookie_authenticates_jaccount_user(self) -> None:
        user = {
            "id": "user-1",
            "username": "student01",
            "displayName": "测试学生",
            "role": "student",
            "authSource": "jaccount",
        }
        token = create_access_token(user)
        request = _request_with_cookies({self.settings.auth_cookie_name: token})

        with patch("app.services.auth.find_user", return_value=user) as find_user:
            authenticated = require_user(request, authorization=None)

        find_user.assert_called_once_with("user-1")
        self.assertEqual(authenticated, user)

    async def test_callback_sets_compass_session_cookie(self) -> None:
        request = _request_with_cookies(
            {
                "siyuan_oauth_state": "expected-state",
                "siyuan_oauth_nonce": "expected-nonce",
                "siyuan_oauth_next": "/shengya/my-reports",
            }
        )
        identity = type(
            "Identity",
            (),
            {"username": "student01", "display_name": "测试学生"},
        )()
        user = {
            "id": "user-1",
            "username": "student01",
            "displayName": "测试学生",
            "role": "student",
            "authSource": "jaccount",
        }

        with (
            patch(
                "app.api.auth.exchange_authorization_code",
                new=AsyncMock(return_value={"id_token": "signed-token"}),
            ) as exchange,
            patch("app.api.auth.decode_identity_token", return_value=identity),
            patch("app.api.auth.upsert_jaccount_user", return_value=user),
        ):
            response = await jaccount_callback(
                request=request,
                code="authorization-code",
                state="expected-state",
                oauth_error=None,
            )

        exchange.assert_awaited_once_with("authorization-code")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "https://ai4edu.sjtu.edu.cn/shengya/my-reports",
        )
        cookies = response.headers.getlist("set-cookie")
        self.assertTrue(any(cookie.startswith("siyuan_session=") for cookie in cookies))
        self.assertTrue(any("HttpOnly" in cookie for cookie in cookies))
        self.assertTrue(any("Secure" in cookie for cookie in cookies))

    async def test_callback_rejects_state_mismatch_before_token_exchange(self) -> None:
        request = _request_with_cookies(
            {
                "siyuan_oauth_state": "expected-state",
                "siyuan_oauth_nonce": "expected-nonce",
            }
        )

        with patch(
            "app.api.auth.exchange_authorization_code",
            new=AsyncMock(),
        ) as exchange:
            response = await jaccount_callback(
                request=request,
                code="authorization-code",
                state="wrong-state",
                oauth_error=None,
            )

        exchange.assert_not_awaited()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/shengya/login?", response.headers["location"])


if __name__ == "__main__":
    unittest.main()
