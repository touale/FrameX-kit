import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import HTTPException, Response
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Route

from framex.config import settings
from framex.consts import API_STR, PROXY_PLUGIN_NAME
from framex.driver.application import create_fastapi_application
from framex.driver.auth import api_key_header
from framex.driver.ingress import APIIngress

# ---------- helpers ----------


def make_route(path: str, methods: set[str]) -> APIRoute:
    route = Mock(spec=APIRoute)
    route.path = path
    route.methods = methods
    return route


# ---------- fixtures ----------


@pytest.fixture
def mock_app():
    with patch("framex.driver.ingress.app") as app:
        app.routes = []
        app.add_api_route = Mock()
        yield app


@pytest.fixture
def ingress():
    return APIIngress.__new__(APIIngress)


# ---------- tests ----------


def test_add_first_route_success(ingress, mock_app):
    endpoint = Mock()

    ingress.add_api_route("/users", endpoint, methods=["GET"])

    mock_app.add_api_route.assert_called_once_with(
        "/users",
        endpoint,
        methods=["GET"],
        tags=None,
        include_in_schema=True,
    )


@pytest.mark.parametrize(
    ("existing_path", "new_path"),
    [
        ("/users/{id}", "/users/{id}"),
        ("/users/{id}", "/users/{user_id}"),
        ("/users/{uid}/posts/{pid}", "/users/{id}/posts/{post_id}"),
    ],
)
def test_duplicate_path_same_method_raises(ingress, mock_app, existing_path, new_path):
    mock_app.routes = [make_route(existing_path, {"GET"})]

    with pytest.raises(RuntimeError, match=r"Duplicate API route"):
        ingress.add_api_route(new_path, Mock(), methods=["GET"])


def test_same_path_different_method_allowed(ingress, mock_app):
    mock_app.routes = [make_route("/users/{id}", {"GET"})]

    ingress.add_api_route("/users/{id}", Mock(), methods=["POST"])

    mock_app.add_api_route.assert_called_once()


def test_overlapping_methods_raises(ingress, mock_app):
    mock_app.routes = [make_route("/users", {"GET", "POST"})]

    with pytest.raises(RuntimeError):
        ingress.add_api_route("/users", Mock(), methods=["POST", "PUT"])


def test_case_insensitive_methods(ingress, mock_app):
    mock_app.routes = [make_route("/users", {"GET"})]

    with pytest.raises(RuntimeError):
        ingress.add_api_route("/users", Mock(), methods=["get"])


def test_non_api_route_is_ignored(ingress, mock_app):
    non_api_route = Mock(spec=Route)
    non_api_route.path = "/users/{id}"
    mock_app.routes = [non_api_route]

    ingress.add_api_route("/users/{id}", Mock(), methods=["GET"])

    mock_app.add_api_route.assert_called_once()


def test_kwargs_are_passed_through(ingress, mock_app):
    ingress.add_api_route(
        "/users",
        Mock(),
        methods=["GET"],
        tags=["users"],
        response_class=Mock(),
    )

    _, kwargs = mock_app.add_api_route.call_args
    assert kwargs["tags"] == ["users"]
    assert "response_class" in kwargs


def test_register_route_allows_business_params_named_request_and_response(ingress, mock_app):
    handle = Mock()
    handle.deployment_name = "demo.Deployment"
    handle.echo = Mock()

    registered = ingress.register_route(
        "/echo",
        ["POST"],
        "echo",
        [("request", str), ("response", str)],
        handle,
        auth_keys=None,
    )

    assert registered is True
    endpoint = mock_app.add_api_route.call_args.args[1]
    signature = endpoint.__signature__
    assert "framex_request" in signature.parameters
    assert "framex_response" in signature.parameters
    assert "request" in signature.parameters
    assert "response" in signature.parameters


def test_register_route_internal_params_avoid_business_param_conflicts(ingress, mock_app):
    handle = Mock()
    handle.deployment_name = "demo.Deployment"
    handle.echo = Mock()

    registered = ingress.register_route(
        "/echo",
        ["POST"],
        "echo",
        [("framex_request", str), ("framex_response", str)],
        handle,
        auth_keys=None,
    )

    assert registered is True
    endpoint = mock_app.add_api_route.call_args.args[1]
    signature = endpoint.__signature__
    assert "framex_request_" in signature.parameters
    assert "framex_response_" in signature.parameters
    assert "framex_request" in signature.parameters
    assert "framex_response" in signature.parameters


def register_stream_endpoint(ingress, mock_app, adapter, auth_keys=None):
    handle = Mock()
    handle.deployment_name = "demo.Deployment"
    handle.stream = Mock()

    with (
        patch("framex.driver.ingress.get_adapter", return_value=adapter),
        patch.object(type(settings.auth), "get_auth_keys", return_value=auth_keys),
    ):
        registered = ingress.register_route(
            "/stream",
            ["GET"],
            "stream",
            [],
            handle,
            stream=True,
            auth_keys=auth_keys,
        )

    assert registered is True
    return mock_app.add_api_route.call_args.args[1]


async def collect_stream_response(endpoint):
    response = await endpoint(framex_request=Mock(), framex_response=Response())
    return [chunk async for chunk in response.body_iterator]


class AwaitableAsyncStream:
    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def __await__(self):
        raise RuntimeError("stream response should not be awaited")
        yield  # pragma: no cover

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._chunks)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


async def test_register_route_stream_does_not_await_async_iterable_response(ingress, mock_app):
    adapter = Mock()
    adapter._stream_call.return_value = AwaitableAsyncStream(["chunk"])
    endpoint = register_stream_endpoint(ingress, mock_app, adapter)

    assert await collect_stream_response(endpoint) == ["chunk"]


async def test_register_route_stream_converts_iteration_error_to_sse_event(ingress, mock_app):
    async def failing_stream():
        yield "first"
        raise RuntimeError("The report is unavailable.\nTry again later.")

    adapter = Mock()
    adapter._stream_call.return_value = failing_stream()
    endpoint = register_stream_endpoint(ingress, mock_app, adapter)

    chunks = await collect_stream_response(endpoint)

    first, event = chunks
    assert first == "first"
    assert event.startswith("event: error\ndata: ")
    assert json.loads(event.removeprefix("event: error\ndata: ")) == {
        "status": 500,
        "message": "The report is unavailable. Try again later.",
        "code": "INTERNAL_SERVER_ERROR",
    }


class StructuredUpstreamError(Exception):
    def __init__(self, status_code, body):
        super().__init__("Private exception wrapper")
        self.status_code = status_code
        self.body = body


class DetailedError(Exception):
    detail = "The report format is unsupported."
    code = "UNSUPPORTED_REPORT_FORMAT"


def register_failing_plugin_route(ingress, monkeypatch, invoke, *, stream=False, deployment_name="demo.Deployment"):
    app = create_fastapi_application()
    monkeypatch.setattr("framex.driver.ingress.app", app)
    handle = SimpleNamespace(deployment_name=deployment_name, invoke=invoke)
    path = f"{API_STR}/test-plugin-error"
    assert ingress.register_route(path, ["GET"], "invoke", [], handle, stream=stream)
    return TestClient(app, raise_server_exceptions=False).get(path)


@pytest.mark.parametrize("mode", ["json", "before_chunk", "after_chunk"])
def test_plugin_error_preserves_structured_fields(ingress, monkeypatch, mode):
    request_id = "test-request-123"
    message = "Revise the input before retrying."
    code = "InputRejected"
    streaming = mode != "json"
    error: Exception
    if streaming:
        request = httpx.Request("GET", "https://upstream.example.test/resource")
        upstream = httpx.Response(
            429,
            request=request,
            json={"message": f"{message} request_id={request_id}", "code": code},
            headers={"X-Request-ID": request_id},
        )
        error = httpx.HTTPStatusError("Private exception wrapper", request=request, response=upstream)
    else:
        error = StructuredUpstreamError(
            400,
            {
                "error": {
                    "message": f"{message}\nRequest ID: {request_id}",
                    "code": code,
                    "debug": "Private diagnostic",
                },
                "request_id": request_id,
            },
        )
    expected = {"status": 429 if streaming else 400, "message": message, "code": code}

    async def fail():
        raise error

    async def failing_stream():
        if mode == "after_chunk":
            yield "event: message_chunk\ndata: chunk\n\n"
        raise error

    response = register_failing_plugin_route(
        ingress, monkeypatch, failing_stream if streaming else fail, stream=streaming
    )

    if streaming:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        if mode == "after_chunk":
            assert response.text.startswith("event: message_chunk\ndata: chunk\n\n")
        assert response.text.count("event: error\n") == 1
        _, _, data = response.text.partition("event: error\ndata: ")
        assert json.loads(data) == expected
    else:
        assert response.status_code == expected["status"]
        payload = response.json()
        assert payload.pop("timestamp")
        assert payload == expected

    for private_value in (request_id, "Private exception wrapper", "Private diagnostic", "Traceback"):
        assert private_value not in response.text


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            StructuredUpstreamError(418, {"error": {"message": ["private"], "code": "malformed code"}}),
            {"status": 418, "message": "I'm a Teapot", "code": "HTTP_418"},
        ),
        (
            StructuredUpstreamError(200, {"detail": "The operation could not be completed."}),
            {"status": 500, "message": "The operation could not be completed.", "code": "INTERNAL_SERVER_ERROR"},
        ),
        (
            ValueError("Invalid date range."),
            {"status": 500, "message": "Invalid date range.", "code": "INTERNAL_SERVER_ERROR"},
        ),
        (
            DetailedError(),
            {"status": 500, "message": "The report format is unsupported.", "code": "UNSUPPORTED_REPORT_FORMAT"},
        ),
        (
            RuntimeError(),
            {"status": 500, "message": "Internal Server Error", "code": "INTERNAL_SERVER_ERROR"},
        ),
    ],
)
def test_plugin_error_uses_safe_fallback(ingress, monkeypatch, error, expected):
    async def fail():
        raise error

    response = register_failing_plugin_route(ingress, monkeypatch, fail)
    assert response.status_code == expected["status"]
    payload = response.json()
    assert payload.pop("timestamp")
    assert payload == expected


def test_plugin_error_uses_explicit_cause_when_wrapper_has_no_message(ingress, monkeypatch):
    async def fail():
        raise RuntimeError from KeyError("report_id")

    response = register_failing_plugin_route(ingress, monkeypatch, fail)

    assert response.status_code == 500
    assert response.json()["message"] == "'report_id'"
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"


def test_non_json_plugin_upstream_error_uses_status_phrase(ingress, monkeypatch):
    request = httpx.Request("GET", "https://upstream.example.test/resource")
    upstream = httpx.Response(502, request=request, text="Private upstream diagnostic")

    async def fail():
        upstream.raise_for_status()

    response = register_failing_plugin_route(ingress, monkeypatch, fail)
    assert response.status_code == 502
    payload = response.json()
    assert payload.pop("timestamp")
    assert payload == {"status": 502, "message": "Bad Gateway", "code": "HTTP_502"}


def test_plugin_explicit_http_exception_keeps_existing_envelope(ingress, monkeypatch):
    async def fail():
        raise HTTPException(status_code=409, detail="Explicit plugin message", headers={"X-Test": "preserved"})

    response = register_failing_plugin_route(ingress, monkeypatch, fail)
    assert response.status_code == 200
    assert response.headers["x-test"] == "preserved"
    payload = response.json()
    assert payload.pop("timestamp")
    assert payload == {"status": 409, "message": "Explicit plugin message"}


def test_builtin_proxy_stream_preserves_existing_error(ingress, monkeypatch):
    async def failing_stream():
        yield "first\n\n"
        raise RuntimeError("Proxy stream failed")

    response = register_failing_plugin_route(
        ingress, monkeypatch, failing_stream, stream=True, deployment_name=PROXY_PLUGIN_NAME
    )

    assert response.status_code == 200
    assert response.text == 'first\n\nevent: error\ndata: {"status": 500, "message": "Proxy stream failed"}\n\n'


async def test_register_route_stream_awaits_generator_factory(ingress, mock_app):
    async def stream_factory(*_, **__):
        async def gen():
            yield "chunk"

        return gen()

    adapter = Mock()
    adapter._stream_call.side_effect = stream_factory
    endpoint = register_stream_endpoint(ingress, mock_app, adapter)

    assert await collect_stream_response(endpoint) == ["chunk"]


async def test_register_route_stream_preserves_sync_generator_support(ingress, mock_app):
    def sync_stream():
        yield "chunk"

    adapter = Mock()
    adapter._stream_call.return_value = sync_stream()
    endpoint = register_stream_endpoint(ingress, mock_app, adapter)

    assert await collect_stream_response(endpoint) == ["chunk"]


async def test_register_route_stream_propagates_cancellation(ingress, mock_app):
    async def cancelled_stream():
        raise asyncio.CancelledError
        yield  # pragma: no cover

    adapter = Mock()
    adapter._stream_call.return_value = cancelled_stream()
    endpoint = register_stream_endpoint(ingress, mock_app, adapter)

    with pytest.raises(asyncio.CancelledError):
        await collect_stream_response(endpoint)


async def test_register_route_stream_converts_auth_error_to_sse_event(ingress, mock_app):
    adapter = Mock()
    endpoint = register_stream_endpoint(ingress, mock_app, adapter, auth_keys=["valid-key"])
    dependency = mock_app.add_api_route.call_args.kwargs["dependencies"][0]
    assert dependency.dependency is api_key_header
    submitted_key = "submitted-secret-api-key"
    request = Mock(headers={"Authorization": submitted_key})

    with patch("framex.driver.ingress.auth_jwt", return_value=False):
        response = await endpoint(framex_request=request, framex_response=Response())
        chunks = [chunk async for chunk in response.body_iterator]

    assert chunks == [
        'event: error\ndata: {"status": 401, "message": "Invalid API Key for API(/stream)"}\n\n',
    ]
    assert submitted_key not in "".join(chunks)
    adapter._stream_call.assert_not_called()
