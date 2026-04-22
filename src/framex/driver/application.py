"""Module containing FastAPI instance related functions and classes."""

import json
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import httpx
import pytz
from fastapi import Body, Depends, FastAPI
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
from framex.repository import (
    can_access_repository,
    get_latest_repository_version,
    has_newer_release_version,
    is_private_repository,
)
from framex.utils import (
    build_docs_action_button_views,
    build_plugin_config_html,
    build_swagger_ui_html,
    collect_embedded_config_files,
    extract_docs_action_response_open_url,
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

    def _get_runtime_plugin_info(plugin_id: str) -> Any | None:
        plugin_info_map = getattr(application.state, "plugin_info_map", None)
        if isinstance(plugin_info_map, dict) and plugin_id in plugin_info_map:
            return plugin_info_map[plugin_id]
        return None

    def _get_docs_action_button(button_index: int) -> Any:
        action_buttons = settings.docs.action_buttons
        if button_index < 0 or button_index >= len(action_buttons):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docs action button not found")
        return action_buttons[button_index]

    def _check_docs_action_button_auth(
        action_button: Any,
        request: Request,
        request_payload: dict[str, Any],
    ) -> None:
        auth_payload = get_auth_payload(request)
        action_auth = action_button.auth
        if action_auth.type == "oauth":
            if auth_payload is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth authentication required")
            if (
                "*" not in action_auth.allowed_usernames
                and auth_payload.get("username") not in action_auth.allowed_usernames
            ):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not allowed")
        elif action_auth.type == "password":
            supplied_auth = request_payload.get("auth", {})
            if not isinstance(supplied_auth, dict) or supplied_auth.get("password") != action_auth.password:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid action password")

    @application.get(DOCS_URL, include_in_schema=False)
    async def get_documentation(_: Annotated[str, Depends(authenticate)]) -> HTMLResponse:
        return build_swagger_ui_html(
            openapi_url=OPENAPI_URL,
            title="FrameX Docs",
            action_buttons=build_docs_action_button_views(settings.docs.action_buttons),
        )

    @application.post("/docs/action-buttons/{button_index}/invoke", include_in_schema=False)
    async def invoke_docs_action_button(
        button_index: int,
        request: Request,
        payload: dict[str, Any] | None = Body(default=None),  # noqa
    ) -> JSONResponse:
        action_button = _get_docs_action_button(button_index)
        if action_button.method == "LINK":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Docs action button is a link")

        request_payload = payload or {}
        _check_docs_action_button_auth(action_button, request, request_payload)

        input_values = request_payload.get("inputs", {})
        if not isinstance(input_values, dict):
            raise HTTPException(status_code=422, detail="Invalid input payload")

        missing_inputs = [
            input_config.label or input_config.name
            for input_config in action_button.inputs
            if input_config.required and not str(input_values.get(input_config.name, "")).strip()
        ]
        if missing_inputs:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required inputs: {', '.join(missing_inputs)}",
            )

        merged_query = dict(action_button.query)
        merged_body = dict(action_button.body)
        for input_config in action_button.inputs:
            if input_config.name in input_values:
                if input_config.target == "query":
                    merged_query[input_config.name] = input_values[input_config.name]
                else:
                    merged_body[input_config.name] = input_values[input_config.name]

        request_kwargs: dict[str, Any] = {"headers": action_button.headers, "params": merged_query}
        if merged_body:
            if action_button.body_type == "form":
                request_kwargs["data"] = merged_body
            else:
                request_kwargs["json"] = merged_body

        try:
            async with httpx.AsyncClient(timeout=action_button.timeout) as client:
                response = await client.request(
                    action_button.method,
                    action_button.url,
                    **request_kwargs,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=safe_error_message(exc)) from exc

        response_content: dict[str, Any] = {
            "ok": response.is_success,
            "status_code": response.status_code,
            "body": response.text,
        }
        if action_button.response_open_url:
            response_content["open_url"] = extract_docs_action_response_open_url(
                response.text,
                action_button.response_open_url,
            )

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_content)

    @application.post("/docs/action-buttons/{button_index}/open", include_in_schema=False)
    async def open_docs_action_button(
        button_index: int,
        request: Request,
        payload: dict[str, Any] | None = Body(default=None),  # noqa
    ) -> JSONResponse:
        action_button = _get_docs_action_button(button_index)
        if action_button.method != "LINK":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Docs action button is not a link")

        request_payload = payload or {}
        _check_docs_action_button_auth(action_button, request, request_payload)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"open_url": action_button.url},
        )

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

        runtime_plugin_info = _get_runtime_plugin_info(plugin)
        auth_payload = get_auth_payload(request)
        repo_url = (
            runtime_plugin_info.repo_url if runtime_plugin_info is not None and runtime_plugin_info.repo_url else ""
        )

        if not repo_url or auth_payload is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Repository access denied: {plugin}")

        repository_is_private = await is_private_repository(repo_url)
        if repository_is_private is not False:
            access_result = await can_access_repository(
                repo_url,
                auth_payload.get("oauth_provider"),
                auth_payload.get("oauth_access_token"),
            )
            if access_result is not True:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"Repository access denied: {plugin}"
                )

        config_data = settings.plugins.get(plugin)
        if config_data is None and runtime_plugin_info is not None and runtime_plugin_info.metadata_name:
            config_data = settings.plugins.get(runtime_plugin_info.metadata_name)
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
        runtime_plugin_info = _get_runtime_plugin_info(plugin)
        if runtime_plugin_info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin not found: {plugin}")

        current_version = runtime_plugin_info.version
        repo_url = runtime_plugin_info.repo_url or ""
        if not current_version or not repo_url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plugin not found: {plugin}")

        current_version = current_version if current_version.startswith("v") else f"v{current_version}"
        latest_version = await get_latest_repository_version(repo_url)
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
