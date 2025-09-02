"""Module containing FastAPI instance related functions and classes."""

import json
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import pytz
from fastapi import FastAPI
from starlette import status
from starlette.concurrency import iterate_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from framex.consts import API_STR, PROJECT_NAME, VERSION


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
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    @application.exception_handler(HTTPException)
    async def _http_exception_handler(request, exc):  # noqa
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "message": exc.detail,
                "is_middleware_error": True,
            },
        )

    @application.exception_handler(Exception)
    async def _general_exception_handler(request, exc):  # noqa
        return JSONResponse(
            status_code=status.HTTP_200_OK,
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
            or request.url.path in ["/docs", "/api/v1/openapi.json"]
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
            status_code=status.HTTP_200_OK,
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
