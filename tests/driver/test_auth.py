import uuid
from datetime import UTC, datetime, timedelta
from http.cookies import SimpleCookie
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from starlette.requests import Request

from framex.config import AuthConfig
from framex.consts import AUTH_COOKIE_NAME, DOCS_URL, OAUTH_STATE_COOKIE_NAME
from framex.driver.application import create_fastapi_application
from framex.driver.auth import (
    auth_jwt,
    authenticate,
    create_auth_session,
    create_jwt,
    create_oauth_redirect,
    decode_auth_token,
    oauth_callback,
)

JWT_SECRET = uuid.uuid4().hex

# =========================================================
# helpers
# =========================================================


def fake_oauth(**overrides):
    data = dict(  # noqa: C408
        provider="gitlab",
        authorization_url="https://oauth.example.com/authorize",
        token_url="https://oauth.example.com/token",  # noqa: S106
        user_info_url="https://oauth.example.com/user",
        client_id="client",
        client_secret="secret",  # noqa: S106
        redirect_uri="/oauth/callback",
        call_back_url="http://testserver/callback",
        app_url="http://testserver",
        jwt_secret=JWT_SECRET,
        jwt_algorithm="HS256",
        use_secure_cookie=False,
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def make_request(path="/docs", cookies=None, query_string="", server=("testserver", 80), scheme="http"):
    cookie_header = "; ".join(f"{name}={value}" for name, value in (cookies or {}).items())
    headers = [(b"cookie", cookie_header.encode())] if cookie_header else []
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": scheme,
            "server": server,
            "client": ("test", 123),
            "path": path,
            "query_string": query_string.encode(),
            "headers": headers,
        }
    )


def begin_oauth(redirect_url=DOCS_URL):
    authorization_url, cookie_header = create_oauth_redirect(redirect_url)
    state = parse_qs(urlparse(authorization_url).query)["state"][0]
    cookies = SimpleCookie()
    cookies.load(cookie_header)
    state_cookie = cookies[OAUTH_STATE_COOKIE_NAME].value
    return authorization_url, state, state_cookie, cookie_header


def decode_state_cookie(state_cookie):
    return jwt.decode(state_cookie, JWT_SECRET, algorithms=["HS256"])


# =========================================================
# create_jwt
# =========================================================


class TestCreateJWT:
    def test_create_jwt_success(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            token = create_jwt({"username": "test"})
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
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
            mock_oauth.jwt_secret = JWT_SECRET
            mock_oauth.jwt_algorithm = "HS256"

            req = Mock(spec=Request)
            req.cookies.get.return_value = None

            assert auth_jwt(req) is False

    def test_returns_true_when_token_is_valid(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = JWT_SECRET
            mock_oauth.jwt_algorithm = "HS256"

            session_id = create_auth_session({"username": "test"})
            token = create_jwt({"username": "test", "session_id": session_id})

            req = Mock(spec=Request)
            req.cookies.get.return_value = token

            assert auth_jwt(req) is True

    def test_returns_false_when_token_is_invalid(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = JWT_SECRET
            mock_oauth.jwt_algorithm = "HS256"

            req = Mock(spec=Request)
            req.cookies.get.return_value = "this.is.not.a.jwt"

            assert auth_jwt(req) is False

    def test_returns_false_when_token_is_expired(self):
        with patch("framex.config.settings.auth.oauth") as mock_oauth:
            mock_oauth.jwt_secret = JWT_SECRET
            mock_oauth.jwt_algorithm = "HS256"

            now = datetime.now(UTC)
            expired_token = jwt.encode(
                {
                    "username": "test",
                    "iat": int((now - timedelta(days=2)).timestamp()),
                    "exp": int((now - timedelta(days=1)).timestamp()),
                },
                JWT_SECRET,
                algorithm="HS256",
            )

            req = Mock(spec=Request)
            req.cookies.get.return_value = expired_token

            assert auth_jwt(req) is False


# =========================================================
# authenticate (unit)
# =========================================================


class TestAuthenticate:
    def test_redirects_to_configured_app_origin_before_starting_oauth(self):
        oauth = fake_oauth(
            app_url="http://localhost:11000",
            call_back_url="http://localhost:11000/oauth/callback",
        )
        request = make_request(
            path="/docs",
            query_string="view=plugins",
            server=("127.0.0.1", 11000),
        )

        with patch("framex.config.settings.auth.oauth", oauth), pytest.raises(HTTPException) as exc:
            authenticate(request, api_key=None)

        assert exc.value.status_code == status.HTTP_302_FOUND
        assert exc.value.headers == {"Location": "http://localhost:11000/docs?view=plugins"}

    def test_redirect_when_no_credentials(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            req = make_request()
            with pytest.raises(HTTPException) as exc:
                authenticate(req, api_key=None)
            assert exc.value.status_code == status.HTTP_302_FOUND
            assert exc.value.headers is not None
            state = parse_qs(urlparse(exc.value.headers["Location"]).query)["state"][0]
            assert state != DOCS_URL
            cookies = SimpleCookie()
            cookies.load(exc.value.headers["Set-Cookie"])
            state_payload = decode_state_cookie(cookies[OAUTH_STATE_COOKIE_NAME].value)
            assert state_payload["state"] == state
            assert state_payload["redirect_url"] == DOCS_URL
            assert "HttpOnly" in exc.value.headers["Set-Cookie"]
            assert "SameSite=lax" in exc.value.headers["Set-Cookie"]

    def test_valid_api_key(self):
        with (
            patch("framex.config.settings.auth.oauth", fake_oauth()),
            patch.object(AuthConfig, "get_auth_keys", return_value=["good-key"]),
        ):
            authenticate(make_request(), api_key="good-key")


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

            _authorization_url, state, state_cookie, _cookie_header = begin_oauth()
            request = make_request(
                path="/oauth/callback",
                cookies={OAUTH_STATE_COOKIE_NAME: state_cookie},
            )
            res = await oauth_callback(request=request, code="abc", state=state)
            assert res.status_code == status.HTTP_302_FOUND
            assert res.headers["location"] == DOCS_URL
            response_cookies = SimpleCookie()
            for cookie_header in res.headers.getlist("set-cookie"):
                response_cookies.load(cookie_header)
            token = response_cookies[AUTH_COOKIE_NAME].value
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            assert payload["oauth_provider"] == "gitlab"
            assert payload["session_id"]
            assert "oauth_access_token" not in payload
            decoded_payload = decode_auth_token(token)
            assert decoded_payload is not None
            assert decoded_payload["oauth_access_token"] == "oauth-token"  # noqa
            set_cookie_headers = res.headers.getlist("set-cookie")
            assert any(
                f"{OAUTH_STATE_COOKIE_NAME}=" in header and "Max-Age=0" in header for header in set_cookie_headers
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_state", [None, "unknown-state"])
    async def test_oauth_callback_rejects_missing_or_unknown_state_before_token_exchange(self, invalid_state):
        with patch("framex.config.settings.auth.oauth", fake_oauth()), patch("httpx.AsyncClient") as mock_client_cls:
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback(make_request(path="/oauth/callback"), code="sensitive-code", state=invalid_state)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "Invalid or expired OAuth state"
            mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_oauth_callback_rejects_mismatched_state(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()), patch("httpx.AsyncClient") as mock_client_cls:
            _authorization_url, _state, state_cookie, _cookie_header = begin_oauth()

            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback(
                    make_request(
                        path="/oauth/callback",
                        cookies={OAUTH_STATE_COOKIE_NAME: state_cookie},
                    ),
                    code="sensitive-code",
                    state="different-state",
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_oauth_callback_rejects_expired_state(self):
        with (
            patch("framex.config.settings.auth.oauth", fake_oauth()),
            patch("framex.driver.auth.OAUTH_STATE_LIFETIME", timedelta(seconds=-1)),
            patch("httpx.AsyncClient") as mock_client_cls,
        ):
            _authorization_url, state, state_cookie, _cookie_header = begin_oauth()

            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback(
                    make_request(path="/oauth/callback", cookies={OAUTH_STATE_COOKIE_NAME: state_cookie}),
                    code="sensitive-code",
                    state=state,
                )

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            mock_client_cls.assert_not_called()

    def test_oauth_redirect_length_is_limited(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            _authorization_url, _state, state_cookie, _cookie_header = begin_oauth(f"/docs?next={'x' * 3_000}")

        assert decode_state_cookie(state_cookie)["redirect_url"] == DOCS_URL


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
            location = resp.headers["location"]
            parsed = urlparse(location)
            assert parsed.hostname == "oauth.example.com"
            assert parse_qs(parsed.query)["scope"] == ["read_user read_api"]

    def test_docs_accessible_with_valid_jwt(self):
        with patch("framex.config.settings.auth.oauth", fake_oauth()):
            app = create_fastapi_application()
            client = TestClient(app)

            session_id = create_auth_session({"username": "test"})
            token = create_jwt({"username": "test", "session_id": session_id})
            client.cookies.set(AUTH_COOKIE_NAME, token)
            resp = client.get("/docs", follow_redirects=False)
            assert resp.status_code == status.HTTP_200_OK
            assert ".swagger-ui .scheme-container .auth-wrapper" in resp.text
            assert ".swagger-ui .scheme-container .authorize" in resp.text
