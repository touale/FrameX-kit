from typing import Any
from unittest.mock import MagicMock

from tests.consts import MOCK_RESPONSE


async def mock_get(_, url: str, *__, **___: Any):
    resp = MagicMock()
    resp.raise_for_status.return_value = None

    if url.endswith("/api/v1/openapi.json"):
        resp.json.return_value = MOCK_RESPONSE
    else:
        raise AssertionError(f"Unexpected request: {url}")

    return resp


async def mock_request(_, method: str, url: str, **kwargs: Any):
    params = kwargs.get("params")
    body = kwargs.get("json") or kwargs.get("data")

    resp = MagicMock()
    resp.raise_for_status.return_value = None
    if url.endswith("/proxy/mock/get") and method == "GET":
        resp.json.return_value = {
            "method": "GET",
            "params": params,
        }
    elif url.endswith("/proxy/mock/post") and method == "POST":
        resp.json.return_value = {
            "method": "POST",
            "params": params,
        }
    elif url.endswith("/proxy/mock/post_model") and method == "POST":
        resp.json.return_value = {
            "method": "POST",
            "body": body,
        }
    elif url.endswith("/proxy/mock/info") and method == "GET":
        resp.json.return_value = {
            "info": "i_am_mock_proxy_info",
        }
    else:
        raise AssertionError(f"Unexpected request: {method} {url}")

    return resp
