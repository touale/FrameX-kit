"""Comprehensive tests for framex.driver.application module."""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

import framex.driver.application as application_module
from framex.config import DocsActionButtonConfig, DocsActionButtonInputConfig, OauthConfig, settings
from framex.consts import API_STR, AUTH_COOKIE_NAME
from framex.driver.application import create_fastapi_application
from framex.driver.auth import create_auth_session, create_jwt


class TestCreateFastAPIApplication:
    """Test suite for create_fastapi_application function."""

    def test_openapi_url_is_none_by_default(self):
        app = create_fastapi_application()
        assert app.openapi_url is None

    def test_docs_url_is_none_by_default(self):
        app = create_fastapi_application()
        assert app.docs_url is None

    def test_redirect_slashes_disabled(self):
        app = create_fastapi_application()
        assert app.router.redirect_slashes is False

    def test_cors_middleware_configured(self):
        app = create_fastapi_application()
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]  # type: ignore
        assert "CORSMiddleware" in middleware_classes


class TestExceptionHandlers:
    @pytest.fixture
    def app(self):
        return create_fastapi_application()

    @pytest.fixture
    def client(self, app):
        return TestClient(app, raise_server_exceptions=False)

    def test_http_exception_handler(self, app, client):
        @app.get("/test-http-exception")
        async def endpoint() -> None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found",
            )

        response = client.get("/test-http-exception")
        data = response.json()

        assert response.status_code == 404
        assert data["status"] == 404
        assert data["message"] == "Not found"
        assert data["is_middleware_error"] is True

    def test_general_exception_handler_returns_500(self, app, client):
        @app.get("/test-general-exception")
        async def endpoint() -> None:
            raise ValueError("Something went wrong")

        response = client.get("/test-general-exception")
        data = response.json()

        assert response.status_code == 500
        assert data["status"] == 500
        assert "Something went wrong" in data["message"]
        assert "timestamp" in data

    def test_unicode_exception_message(self, app, client):
        @app.get("/test-unicode")
        async def endpoint() -> None:
            raise RuntimeError("错误信息 你好 🌍")

        response = client.get("/test-unicode")
        data = response.json()

        assert response.status_code == 500
        assert "你好" in data["message"]
        assert "🌍" in data["message"]


class TestLogResponseMiddleware:
    @pytest.fixture
    def app(self):
        return create_fastapi_application()

    @pytest.fixture
    def client(self, app):
        return TestClient(app, raise_server_exceptions=False)

    def test_api_response_wrapped(self, app, client):
        @app.get(f"{API_STR}/test-wrap")
        async def endpoint() -> Any:
            return {"result": "ok"}

        response = client.get(f"{API_STR}/test-wrap")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == 200
        assert data["message"] == "success"
        assert data["data"] == {"result": "ok"}
        assert "timestamp" in data


class TestDocsActionButtons:
    @staticmethod
    def _get_invoke_endpoint(app) -> Any:
        return next(
            route.endpoint
            for route in app.routes
            if getattr(route, "path", "") == "/docs/action-buttons/{button_index}/invoke"
        )

    @staticmethod
    def _build_request(auth_token: str | None = None) -> Request:
        headers = []
        if auth_token:
            headers.append((b"cookie", f"{AUTH_COOKIE_NAME}={auth_token}".encode()))
        return Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/docs/action-buttons/0/invoke",
                "headers": headers,
            }
        )

    @staticmethod
    def _build_oauth_request(monkeypatch, username: str) -> Request:
        monkeypatch.setattr(
            settings.auth,
            "oauth",
            OauthConfig(jwt_secret="test-secret-with-enough-bytes-for-hs256", jwt_algorithm="HS256"),  # noqa: S106
        )
        session_id = create_auth_session({"username": username})
        token = create_jwt({"session_id": session_id, "username": username})
        return TestDocsActionButtons._build_request(token)

    @staticmethod
    def _patch_fake_http_client(monkeypatch) -> dict[str, Any]:
        captured_request: dict[str, Any] = {}

        class FakeResponse:
            is_success = True
            status_code = 200
            text = "ok"

        class FakeClient:
            def __init__(self, timeout: float):
                captured_request["timeout"] = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
                captured_request.update({"method": method, "url": url, "kwargs": kwargs})
                return FakeResponse()

        monkeypatch.setattr(application_module.httpx, "AsyncClient", FakeClient)
        return captured_request

    @pytest.mark.asyncio
    async def test_invoke_form_action_button_merges_body_inputs(self, monkeypatch):
        captured_request: dict[str, Any] = {}

        class FakeResponse:
            is_success = True
            status_code = 201
            text = "created"

        class FakeClient:
            def __init__(self, timeout: float):
                captured_request["timeout"] = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
                captured_request.update({"method": method, "url": url, "kwargs": kwargs})
                return FakeResponse()

        monkeypatch.setattr(application_module.httpx, "AsyncClient", FakeClient)
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Trigger CI",
                    url="https://example.test/trigger",
                    method="POST",
                    auth={"type": "none"},
                    body_type="form",
                    body={
                        "token": "secret-token",
                        "ref": "test-ci",
                        "variables[PACKAGE_NAME]": "task-decomposer",
                    },
                    inputs=[
                        DocsActionButtonInputConfig(
                            name="variables[PACKAGE_VERSION]",
                            label="Package Version",
                            required=True,
                        )
                    ],
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())
        response = await endpoint(
            0,
            self._build_request(),
            {"inputs": {"variables[PACKAGE_VERSION]": "0.0.8"}},
        )

        assert response.status_code == status.HTTP_200_OK
        assert captured_request == {
            "method": "POST",
            "url": "https://example.test/trigger",
            "timeout": 30.0,
            "kwargs": {
                "headers": {},
                "params": {},
                "data": {
                    "token": "secret-token",
                    "ref": "test-ci",
                    "variables[PACKAGE_NAME]": "task-decomposer",
                    "variables[PACKAGE_VERSION]": "0.0.8",
                },
            },
        }

    @pytest.mark.asyncio
    async def test_invoke_get_action_button_merges_query_inputs(self, monkeypatch):
        captured_request: dict[str, Any] = {}

        class FakeResponse:
            is_success = True
            status_code = 200
            text = '{"message":"asd"}'

        class FakeClient:
            def __init__(self, timeout: float):
                captured_request["timeout"] = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return None

            async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
                captured_request.update({"method": method, "url": url, "kwargs": kwargs})
                return FakeResponse()

        monkeypatch.setattr(application_module.httpx, "AsyncClient", FakeClient)
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    method="GET",
                    timeout=12.5,
                    auth={"type": "none"},
                    headers={"accept": "application/json", "Authorization": "888"},
                    inputs=[
                        DocsActionButtonInputConfig(
                            name="message",
                            label="Message",
                            required=True,
                            target="query",
                        )
                    ],
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())
        response = await endpoint(0, self._build_request(), {"inputs": {"message": "asd"}})

        assert response.status_code == status.HTTP_200_OK
        assert captured_request == {
            "method": "GET",
            "url": "http://localhost:11000/api/v1/echo",
            "timeout": 12.5,
            "kwargs": {
                "headers": {"accept": "application/json", "Authorization": "888"},
                "params": {"message": "asd"},
            },
        }

    @pytest.mark.asyncio
    async def test_invoke_action_button_rejects_missing_required_input(self, monkeypatch):
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "none"},
                    inputs=[
                        DocsActionButtonInputConfig(
                            name="message",
                            label="Message",
                            required=True,
                            target="query",
                        )
                    ],
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(0, self._build_request(), {"inputs": {"message": ""}})

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "Missing required inputs: Message"

    @pytest.mark.asyncio
    async def test_invoke_action_button_rejects_missing_oauth_session(self, monkeypatch):
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "oauth"},
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(0, self._build_request(), {"inputs": {}})

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "OAuth authentication required"

    @pytest.mark.asyncio
    async def test_invoke_action_button_allows_oauth_wildcard_user(self, monkeypatch):
        captured_request = self._patch_fake_http_client(monkeypatch)
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "oauth", "allowed_usernames": ["*"]},
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())
        response = await endpoint(0, self._build_oauth_request(monkeypatch, "anyone"), {"inputs": {}})

        assert response.status_code == status.HTTP_200_OK
        assert captured_request["url"] == "http://localhost:11000/api/v1/echo"

    @pytest.mark.asyncio
    async def test_invoke_action_button_rejects_oauth_user_not_in_whitelist(self, monkeypatch):
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "oauth", "allowed_usernames": ["alice"]},
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(0, self._build_oauth_request(monkeypatch, "bob"), {"inputs": {}})

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "User is not allowed"

    @pytest.mark.asyncio
    async def test_invoke_action_button_rejects_wrong_password(self, monkeypatch):
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "password", "password": "secret"},
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())

        with pytest.raises(HTTPException) as exc_info:
            await endpoint(0, self._build_request(), {"inputs": {}, "auth": {"password": "wrong"}})

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid action password"

    @pytest.mark.asyncio
    async def test_invoke_action_button_allows_correct_password(self, monkeypatch):
        captured_request = self._patch_fake_http_client(monkeypatch)
        monkeypatch.setattr(
            settings.docs,
            "action_buttons",
            [
                DocsActionButtonConfig(
                    title="Echo",
                    url="http://localhost:11000/api/v1/echo",
                    auth={"type": "password", "password": "secret"},
                )
            ],
        )

        endpoint = self._get_invoke_endpoint(create_fastapi_application())
        response = await endpoint(0, self._build_request(), {"inputs": {}, "auth": {"password": "secret"}})

        assert response.status_code == status.HTTP_200_OK
        assert captured_request["url"] == "http://localhost:11000/api/v1/echo"


class TestLifespanBehavior:
    @patch("framex.config.settings")
    def test_lifespan_without_ray(self, mock_settings):
        mock_settings.server.use_ray = False
        app = create_fastapi_application()
        assert app.router.lifespan_context is not None

    @patch("framex.config.settings")
    def test_lifespan_with_ray(self, mock_settings):
        mock_settings.server.use_ray = True
        app = create_fastapi_application()
        assert app.router.lifespan_context is not None
