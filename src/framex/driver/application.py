"""Module containing FastAPI instance related functions and classes."""

import json
from contextlib import asynccontextmanager
from datetime import datetime

import pytz
from fastapi import FastAPI
from starlette import status
from starlette.concurrency import iterate_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from framex import __version__


def create_fastapi_application() -> FastAPI:
    """
    Create a FastAPI instance.

    Returns
    -------
        object of FastAPI: the fastapi application instance.

    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa
        yield

    application = FastAPI(
        title="123",
        debug=False,
        version=__version__,
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

    async def log_response(request: Request, call_next):
        response = await call_next(request)
        if (
            not request.url.path.startswith("/api")
            or request.url.path in ["/docs", "/api/v1/openapi.json"]
            or b"text/event-stream; charset=utf-8" in response.raw_headers[0]
        ):
            return response

        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        response_body = json.loads(response_body[0].decode())
        if isinstance(response_body, dict) and response_body.get("is_middleware_error", False):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": response_body["status"],
                    "message": response_body["message"],
                    "timestamp": pytz.timezone("Asia/Shanghai").localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": response.status_code,
                "message": "success",
                "timestamp": pytz.timezone("Asia/Shanghai").localize(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
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
