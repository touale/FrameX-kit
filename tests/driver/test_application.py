"""Comprehensive tests for framex.driver.application module."""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette import status
from starlette.exceptions import HTTPException

from framex.consts import API_STR, DOCS_URL, OPENAPI_URL
from framex.driver.application import create_fastapi_application


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


class TestAuthenticationEndpoints:
    @pytest.fixture
    def app(self):
        return create_fastapi_application()

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_docs_requires_auth(self, client):
        response = client.get(DOCS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_docs_wrong_credentials(self, client):
        response = client.get(DOCS_URL, auth=("bad", "bad"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_docs_correct_credentials(self, client):
        from framex.config import settings

        response = client.get(
            DOCS_URL,
            auth=(settings.server.docs_user, settings.server.docs_password),
        )
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_openapi_correct_credentials(self, client):
        from framex.config import settings

        response = client.get(
            OPENAPI_URL,
            auth=(settings.server.docs_user, settings.server.docs_password),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["info"]["title"] == "FrameX API"


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

    def test_docs_not_wrapped(self, client):
        from framex.config import settings

        response = client.get(
            DOCS_URL,
            auth=(settings.server.docs_user, settings.server.docs_password),
        )
        assert "text/html" in response.headers["content-type"]


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
