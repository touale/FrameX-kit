from typing import Any
from unittest.mock import MagicMock

from framex.utils import cache_decode
from tests.consts import MOCK_RESPONSE


async def mock_get(_, url: str, *__, **kwargs: Any):
    resp = MagicMock()
    resp.raise_for_status.return_value = None

    headers = kwargs.get("headers", {})
    if headers.get("Authorization") != "i_am_proxy_docs_auth_keys":
        resp.json.return_value = {
            "status": 401,
            "message": f"Invalid API Key({headers.get('Authorization')}) for API(/api/v1/proxy/mock/auth/get)",
        }
    elif url.endswith("/api/v1/openapi.json"):
        resp.json.return_value = MOCK_RESPONSE
    else:
        raise AssertionError(f"Unexpected request: {url}")

    return resp


async def mock_request(_, method: str, url: str, **kwargs: Any):
    params = kwargs.get("params")
    body = kwargs.get("json") or kwargs.get("data")
    headers = kwargs.get("headers", {})

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
    elif url.endswith("/proxy/mock/auth/get") and method == "GET":
        if headers.get("Authorization") != "i_am_proxy_general_auth_keys":
            resp.json.return_value = {
                "status": 401,
                "message": f"Invalid API Key({headers.get('Authorization')}) for API(/api/v1/proxy/mock/auth/get)",
            }
        else:
            resp.json.return_value = {
                "method": "GET",
                "params": params,
            }
    elif url.endswith("/proxy/mock/auth/sget") and method == "GET":
        if headers.get("Authorization") != "i_am_proxy_special_auth_keys":
            resp.json.return_value = {
                "status": 401,
                "message": f"Invalid API Key({headers.get('Authorization')}) for API(/api/v1/proxy/mock/auth/get)",
            }
        else:
            resp.json.return_value = {
                "method": "GET",
                "params": params,
            }
    elif url.endswith("/proxy/remote") and method == "POST":
        if headers.get("Authorization") != "i_am_proxy_func_auth_keys":
            resp.json.return_value = {
                "status": 401,
                "message": f"Invalid API Key({headers.get('Authorization')}) for API(/api/v1/proxy/mock/auth/get)",
            }
        else:
            json_data = kwargs.get("json", {})
            func_name = json_data.get("func_name")
            data = json_data.get("data", {})
            if not func_name or not data:
                raise ValueError("Missing required fields: func_name and data")
            decode_func_name = cache_decode(func_name)
            decode_data = cache_decode(data)
            resp.json.return_value = {"result": decode_func_name, "data": decode_data}
    else:
        raise AssertionError(f"Unexpected request: {method} {url}")

    return resp
