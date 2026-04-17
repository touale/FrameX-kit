"""Module containing FastAPI instance related functions and classes."""

import json
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import pytz
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.concurrency import iterate_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from framex.config import settings
from framex.consts import API_PRE_STR, DOCS_URL, OPENAPI_URL, PROJECT_NAME, REDOC_URL, VERSION
from framex.driver.auth import authenticate, get_auth_payload, oauth_callback
from framex.plugin import get_plugin
from framex.repository import (
    can_access_repository,
    get_latest_repository_version,
    has_newer_release_version,
    is_private_repository,
)
from framex.utils import (
    build_plugin_config_html,
    build_swagger_ui_html,
    collect_embedded_config_files,
    format_uptime,
    safe_error_message,
)

FRAME_START_TIME = datetime.now(tz=UTC)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
REVERSION = settings.server.reversion or os.getenv("REVERSION")


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
| Service-Version | `v{REVERSION}` |
| FrameX-Version | `v{VERSION}` |

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

            deployments: list[Any] = list(app.state.deployments_dict.values())

            @logger.catch
            async def _on_start(deployment: Any) -> None:
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

    application.state.tags_metadata_map = []

    if settings.auth.oauth:
        application.add_api_route(
            settings.auth.oauth.redirect_uri,
            oauth_callback,
            methods=["GET"],
            include_in_schema=False,
        )

    @application.get(DOCS_URL, include_in_schema=False)
    async def get_documentation(_: Annotated[str, Depends(authenticate)]) -> HTMLResponse:
        return build_swagger_ui_html(openapi_url=OPENAPI_URL, title="FrameX Docs")

    @application.get("/docs/plugin-config", include_in_schema=False)
    async def get_plugin_config_documentation(
        request: Request,
        plugin: str,
        _: Annotated[str, Depends(authenticate)],
    ) -> HTMLResponse:
        if not settings.auth.oauth:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Plugin config documentation requires auth"
            )

        loaded_plugin = get_plugin(plugin)
        auth_payload = get_auth_payload(request)
        repo_url = (
            loaded_plugin.metadata.url if loaded_plugin is not None and loaded_plugin.metadata is not None else ""
        )

        if not repo_url or auth_payload is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Repository access denied: {plugin}")

        repository_is_private = is_private_repository(repo_url)
        if repository_is_private is not False:
            access_result = can_access_repository(
                repo_url,
                auth_payload.get("oauth_provider"),
                auth_payload.get("oauth_access_token"),
            )
            if access_result is not True:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"Repository access denied: {plugin}"
                )

        loaded_config = loaded_plugin.config.model_dump() if loaded_plugin and loaded_plugin.config else None
        config_data = loaded_config or settings.plugins.get(plugin)  # type: ignore
        if config_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin config not found: {plugin}")

        return build_plugin_config_html(
            config_data,
            collect_embedded_config_files(
                config_data,
                workspace_root=Path.cwd().resolve(),
                whitelist=settings.docs.embedded_config_file_whitelist,
            ),
        )

    @application.get("/docs/plugin-release", include_in_schema=False)
    async def get_plugin_release_documentation(
        plugin: str,
        _: Annotated[str, Depends(authenticate)],
    ) -> dict[str, Any]:
        loaded_plugin = get_plugin(plugin)
        if loaded_plugin is None or loaded_plugin.metadata is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin not found: {plugin}")

        current_version = loaded_plugin.metadata.version
        current_version = current_version if current_version.startswith("v") else f"v{current_version}"
        repo_url = loaded_plugin.metadata.url
        latest_version = get_latest_repository_version(repo_url)
        if not latest_version or not has_newer_release_version(current_version, latest_version):
            return {"has_update": False, "latest_version": None, "repo_url": repo_url}
        return {"has_update": True, "latest_version": latest_version, "repo_url": repo_url}

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
            tags=application.state.tags_metadata_map,
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
                "message": safe_error_message(exc),
                "timestamp": pytz.timezone("Asia/Shanghai").localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    async def log_response(request: Request, call_next: Callable) -> Any:  # pragma: no cover
        response = await call_next(request)
        if (
            not request.url.path.startswith(API_PRE_STR)
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
                "message": "success" if response.status_code == 200 else "unexpected code",
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
