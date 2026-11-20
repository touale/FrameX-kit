import re
import sys
from collections.abc import Iterable, Iterator
from contextlib import suppress
from http import HTTPStatus
from itertools import chain
from typing import Any, TypedDict

import httpx

from framex.utils.common import shorten_str


class _PluginError(TypedDict):
    status: int
    message: str
    code: str


def _error_body(error: Exception, response: httpx.Response | None) -> dict[str, Any]:
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        return body
    if response is None:
        return {}
    try:
        body = response.json()
    except (ValueError, httpx.ResponseNotRead, RecursionError):
        return {}
    return body if isinstance(body, dict) else {}


def _public_message(value: object, *request_ids: object) -> str:
    if not isinstance(value, str):
        return ""
    message = "".join(char if char.isprintable() else " " for char in value)
    for request_id in request_ids:
        if isinstance(request_id, str) and request_id.strip():
            token = re.escape(request_id.strip())
            message = re.sub(rf"(?<!\w)(?:(?i:request[ _-]?id)\s*[:=]\s*)?{token}(?!\w)", "", message)
    return shorten_str(" ".join(message.split()).strip(" ,;:-"), 512)


def _http_error_status(value: object) -> int | None:
    return value if isinstance(value, int) and 400 <= value <= 599 else None


def _exception_messages(error: Exception) -> Iterator[object]:
    yield getattr(error, "detail", None)
    yield getattr(error, "message", None)
    for cause in (error, error.__cause__):
        if isinstance(cause, Exception) and not getattr(cause, "traceback_str", None):
            with suppress(Exception):
                yield str(cause)


def format_plugin_error(error: Exception) -> _PluginError:
    # A Ray task error holds the original exception. Local mode need not import Ray.
    task_error_type = getattr(sys.modules.get("ray.exceptions"), "RayTaskError", None)
    if task_error_type is not None and isinstance(error, task_error_type) and isinstance(error.cause, Exception):
        error = error.cause

    response = getattr(error, "response", None)
    if not isinstance(response, httpx.Response):
        response = None
    upstream_status = _http_error_status(getattr(error, "status_code", None))
    if upstream_status is None and response is not None:
        upstream_status = _http_error_status(response.status_code)
    status = upstream_status or HTTPStatus.INTERNAL_SERVER_ERROR

    body = _error_body(error, response)
    nested_error = body.get("error")
    fields = nested_error if isinstance(nested_error, dict) else body
    request_ids = (
        fields.get("request_id"),
        body.get("request_id"),
        getattr(error, "request_id", None),
        response.headers.get("x-request-id") if response is not None else None,
    )
    messages: Iterable[object] = (
        fields.get("message"),
        fields.get("detail"),
        body.get("message"),
        body.get("detail"),
        nested_error,
    )
    # HTTP clients may include a raw response or URL in their exception text.
    if response is None and (upstream_status is None or not body):
        messages = chain(messages, _exception_messages(error))

    for candidate in messages:
        if message := _public_message(candidate, *request_ids):
            break
    else:
        try:
            message = HTTPStatus(status).phrase
        except ValueError:
            message = "Request failed"

    code = fields.get("code") or getattr(error, "code", None)
    if not isinstance(code, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", code) is None:
        code = f"HTTP_{status}" if upstream_status else "INTERNAL_SERVER_ERROR"
    return {"status": status, "message": message, "code": code}
