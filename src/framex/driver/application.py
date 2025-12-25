"""Module containing FastAPI instance related functions and classes."""

import json
import secrets
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import pytz
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status
from starlette.concurrency import iterate_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from framex.config import settings
from framex.consts import API_STR, DOCS_URL, OPENAPI_URL, PROJECT_NAME, REDOC_URL, VERSION
from framex.utils import format_uptime

FRAME_START_TIME = datetime.now(tz=UTC)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def build_openapi_description() -> str:
    now = datetime.now(tz=UTC)
    uptime = format_uptime(now - FRAME_START_TIME)
    started_at = FRAME_START_TIME.astimezone(SHANGHAI_TZ).strftime("%Y-%m-%d %H:%M:%S")
    return f"""
---

**🟢 Runtime Status**

| Metric | Value |
|--------|-------|
| Started At | `{started_at}` |
| Uptime | `{uptime}` |
| Version | `v{VERSION}` |

---
"""


def create_fastapi_application() -> FastAPI:
    """
    Create a FastAPI instance.

    Returns
    -------
        object of FastAPI: the fastapi application instance.

    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa
        from framex.config import settings

        if not settings.server.use_ray:
            from framex.log import logger

            logger.info("Starting FastAPI application...")

            import asyncio

            from ray.serve.handle import DeploymentHandle

            deployments: list[DeploymentHandle] = list(app.state.deployments_dict.values())

            @logger.catch
            async def _on_start(deployment: DeploymentHandle) -> None:
                func = getattr(deployment, "on_start")
                await func()

            for deployment in deployments:
                asyncio.create_task(_on_start(deployment))  # noqa

        yield

    application = FastAPI(
        title=PROJECT_NAME,
        debug=False,
        version=VERSION,
        openapi_url=None,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        redirect_slashes=False,
    )

    security = HTTPBasic(realm="Swagger Docs")

    def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> str:
        correct_username = secrets.compare_digest(credentials.username, settings.server.docs_user)
        correct_password = secrets.compare_digest(credentials.password, settings.server.docs_password)

        if not (correct_username and correct_password):
            from framex.log import logger

            logger.warning(f"Failed authentication attempt for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect user or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

    @application.get(DOCS_URL, include_in_schema=False)
    async def get_documentation(_: Annotated[str, Depends(authenticate)]) -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=OPENAPI_URL, title="FrameX Docs")

    @application.get(REDOC_URL, include_in_schema=False)
    async def get_redoc_documentation(_: Annotated[str, Depends(authenticate)]) -> HTMLResponse:
        return get_redoc_html(openapi_url=OPENAPI_URL, title="FrameX Redoc")

    @application.get(OPENAPI_URL, include_in_schema=False)
    async def get_open_api_endpoint(_: Annotated[str, Depends(authenticate)]) -> dict[str, Any]:
        return get_openapi(
            title="FrameX API",
            version=VERSION,
            description=build_openapi_description(),
            routes=application.routes,
        )

    @application.exception_handler(HTTPException)
    async def _http_exception_handler(request, exc):  # noqa
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "message": exc.detail,
                "is_middleware_error": True,
            },
            headers=headers,
        )

    @application.exception_handler(Exception)
    async def _general_exception_handler(request, exc):  # noqa
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": 500,
                "message": str(exc),
                "timestamp": pytz.timezone("Asia/Shanghai").localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    async def log_response(request: Request, call_next: Callable) -> Any:  # pragma: no cover
        response = await call_next(request)
        if (
            not request.url.path.startswith(API_STR)
            or request.url.path in [DOCS_URL, OPENAPI_URL, *settings.server.excluded_log_paths]
            or b"text/event-stream; charset=utf-8" in response.raw_headers[0]
            or response.headers.get("X-Raw-Output", "False") == "True"
        ):
            return response
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        response_body = json.loads(response_body[0].decode())
        timestamp = pytz.timezone("Asia/Shanghai").localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(response_body, dict) and response_body.get("is_middleware_error", False):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": response_body["status"],
                    "message": response_body["message"],
                    "timestamp": timestamp,
                },
            )
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status": response.status_code,
                "message": "success",
                "timestamp": timestamp,
                "data": response_body,
            },
        )

    application.add_middleware(BaseHTTPMiddleware, dispatch=log_response)
    application.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return application
