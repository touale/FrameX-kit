from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from starlette.requests import Request

from framex.config import AuthConfig
from framex.consts import DOCS_URL
from framex.driver.application import create_fastapi_application
from framex.driver.auth import auth_jwt, authenticate, create_jwt, oauth_callback

# =========================================================
# helpers
# =========================================================


def fake_oauth(**overrides):
    data = dict(  # noqa: C408
        authorization_url="https://oauth.example.com/authorize",
        token_url="https://oauth.example.com/token",  # noqa: S106
        user_info_url="https://oauth.example.com/user",
        client_id="client",
        client_secret="secret",  # noqa: S106
        redirect_uri="/oauth/callback",
        call_back_url="http://test/callback",
        jwt_secret="secret",  # noqa: S106
        jwt_algorithm="HS256",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


# =========================================================
# create_jwt
# =========================================================


class TestCreateJWT:
    def test_create_jwt_success(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            token = create_jwt({"username": "test"})
            decoded = jwt.decode(token, "secret", algorithms=["HS256"])
            assert decoded["username"] == "test"
            assert "iat" in decoded
            assert "exp" in decoded

    def test_create_jwt_no_oauth(self):
        with patch("framex.config.settings.auth.oauth", None), pytest.raises(RuntimeError):
            create_jwt({"username": "test"})


# =========================================================
# auth_jwt
# =========================================================


class TestAuthJWT:
    def test_returns_false_when_oauth_not_configured(self):
        with patch("framex.config.settings.auth.oauth", None):
            req = Mock(spec=Request)
            assert auth_jwt(req) is False

    def test_returns_false_when_no_token_cookie(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = "secret"  # noqa: S105
            mock_oauth.jwt_algorithm = "HS256"

            req = Mock(spec=Request)
            req.cookies.get.return_value = None

            assert auth_jwt(req) is False

    def test_returns_true_when_token_is_valid(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = "secret"  # noqa: S105
            mock_oauth.jwt_algorithm = "HS256"

            now = datetime.now(UTC)
            token = jwt.encode(
                {
                    "username": "test",
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(hours=1)).timestamp()),
                },
                "secret",
                algorithm="HS256",
            )

            req = Mock(spec=Request)
            req.cookies.get.return_value = token

            assert auth_jwt(req) is True

    def test_returns_false_when_token_is_invalid(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = "secret"  # noqa: S105
            mock_oauth.jwt_algorithm = "HS256"

            req = Mock(spec=Request)
            req.cookies.get.return_value = "this.is.not.a.jwt"

            assert auth_jwt(req) is False

    def test_returns_false_when_token_is_expired(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = "secret"  # noqa: S105
            mock_oauth.jwt_algorithm = "HS256"

            now = datetime.now(UTC)
            expired_token = jwt.encode(
                {
                    "username": "test",
                    "iat": int((now - timedelta(days=2)).timestamp()),
                    "exp": int((now - timedelta(days=1)).timestamp()),
                },
                "secret",
                algorithm="HS256",
            )

            req = Mock(spec=Request)
            req.cookies.get.return_value = expired_token

            assert auth_jwt(req) is False


# =========================================================
# authenticate (unit)
# =========================================================


class TestAuthenticate:
    def test_redirect_when_no_credentials(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            req = Mock(spec=Request)
            req.cookies.get.return_value = None
            req.url.path = "/docs"
            with pytest.raises(HTTPException) as exc:
                authenticate(req, api_key=None)
            assert exc.value.status_code == status.HTTP_302_FOUND

    def test_valid_api_key(self):
        with (
            patch("framex.config.settings.auth.oauth", fake_oauth()),
            patch.object(AuthConfig, "get_auth_keys", return_value=["good-key"]),
        ):
            req = Mock(spec=Request)
            req.cookies.get.return_value = None
            req.url.path = "/docs"
            authenticate(req, api_key="good-key")


# =========================================================
# oauth_callback
# =========================================================


class TestOAuthCallback:
    @pytest.mark.asyncio
    async def test_oauth_callback_success(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()), patch("httpx.AsyncClient") as mock_client_cls:
            client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = client

            token_resp = Mock()
            token_resp.json.return_value = {"access_token": "oauth-token"}
            token_resp.raise_for_status = Mock()

            user_resp = Mock()
            user_resp.json.return_value = {"username": "test", "email": "a@b.com"}
            user_resp.raise_for_status = Mock()

            client.post.return_value = token_resp
            client.get.return_value = user_resp

            res = await oauth_callback(code="abc")
            assert res.status_code == status.HTTP_302_FOUND
            assert res.headers["location"] == DOCS_URL
            assert "token=" in res.headers.get("set-cookie", "")


# =========================================================
# Integration
# =========================================================


class TestAuthenticationIntegration:
    def test_docs_redirects_when_not_authenticated(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            app = create_fastapi_application()
            client = TestClient(app)

            resp = client.get("/docs", follow_redirects=False)

            assert resp.status_code == status.HTTP_302_FOUND
            assert "oauth.example.com" in resp.headers["location"]

    def test_docs_accessible_with_valid_jwt(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            app = create_fastapi_application()
            client = TestClient(app)

            now = datetime.now(UTC)
            token = jwt.encode(
                {
                    "username": "test",
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(hours=1)).timestamp()),
                },
                "secret",
                algorithm="HS256",
            )
            client.cookies.set("token", token)
            resp = client.get("/docs", follow_redirects=False)
            assert resp.status_code == status.HTTP_200_OK
