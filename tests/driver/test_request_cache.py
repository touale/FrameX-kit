import hashlib
from typing import Any

import pytest
from starlette.requests import Request
from starlette.responses import Response

from framex.config import settings
from framex.consts import CACHE_KEY_HEADER, CACHE_REQUEST_HEADER, CACHE_STATUS_HEADER
from framex.driver.cache import RequestCache


def _request(method: str = "GET", path: str = "/api/v1/cache-test", headers: dict[str, str] | None = None) -> Request:
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({"type": "http", "method": method, "path": path, "headers": raw_headers})


@pytest.fixture
async def cache(monkeypatch, tmp_path):
    monkeypatch.setattr(settings.cache, "enabled", True)
    monkeypatch.setattr(settings.cache, "mode", "memory")
    monkeypatch.setattr(settings.cache, "ttl", 60)
    monkeypatch.setattr(settings.cache, "max_size", 1000)
    monkeypatch.setattr(settings.cache, "file_dir", str(tmp_path))
    request_cache = RequestCache()
    yield request_cache
    await request_cache.clear()


@pytest.mark.asyncio
async def test_cache_disabled_bypasses(cache, monkeypatch):
    monkeypatch.setattr(settings.cache, "enabled", False)
    calls = 0

    async def invoke() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    first = await cache.call(
        request=_request(),
        response=Response(),
        path="/api/v1/cache-test",
        cache_config={"ttl": 60},
        request_kwargs={"message": "a"},
        invoke=invoke,
    )
    response = Response()
    second = await cache.call(
        request=_request(),
        response=response,
        path="/api/v1/cache-test",
        cache_config={"ttl": 60},
        request_kwargs={"message": "a"},
        invoke=invoke,
    )

    assert first == {"calls": 1}
    assert second == {"calls": 2}
    assert response.headers[CACHE_STATUS_HEADER] == "DISABLED"


@pytest.mark.asyncio
async def test_memory_cache_hits_same_request(cache):
    calls = 0

    async def invoke() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    first_response = Response()
    first = await cache.call(
        request=_request(),
        response=first_response,
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={"message": "a"},
        invoke=invoke,
    )
    second_response = Response()
    second = await cache.call(
        request=_request(),
        response=second_response,
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={"message": "a"},
        invoke=invoke,
    )

    assert first == {"calls": 1}
    assert second == {"calls": 1}
    assert first_response.headers[CACHE_STATUS_HEADER] == "MISS"
    assert second_response.headers[CACHE_STATUS_HEADER] == "HIT"
    assert second_response.headers[CACHE_KEY_HEADER]


@pytest.mark.asyncio
async def test_header_bypass_skips_read_but_writes(cache):
    calls = 0

    async def invoke() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    await cache.call(
        request=_request(),
        response=Response(),
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )
    bypass_response = Response()
    bypassed = await cache.call(
        request=_request(headers={CACHE_REQUEST_HEADER: "bypass"}),
        response=bypass_response,
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )
    hit_response = Response()
    cached = await cache.call(
        request=_request(),
        response=hit_response,
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )

    assert bypassed == {"calls": 2}
    assert cached == {"calls": 2}
    assert bypass_response.headers[CACHE_STATUS_HEADER] == "MISS"
    assert hit_response.headers[CACHE_STATUS_HEADER] == "HIT"


@pytest.mark.asyncio
async def test_header_refresh_overwrites_cache(cache):
    calls = 0

    async def invoke() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    await cache.call(
        request=_request(),
        response=Response(),
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )
    refresh_response = Response()
    refreshed = await cache.call(
        request=_request(headers={CACHE_REQUEST_HEADER: "refresh"}),
        response=refresh_response,
        path="/api/v1/cache-test",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )

    assert refreshed == {"calls": 2}
    assert refresh_response.headers[CACHE_STATUS_HEADER] == "REFRESH"


@pytest.mark.asyncio
async def test_custom_key_builder_receives_context(cache):
    seen_keys: list[list[str]] = []

    def build_key(request: Request, context: Any) -> str:
        seen_keys.append(context.keys())
        return request.url.path

    async def invoke() -> dict[str, str]:
        return {"result": "ok"}

    await cache.call(
        request=_request(),
        response=Response(),
        path="/api/v1/cache-test",
        cache_config={"key_builder": build_key},
        request_kwargs={"message": "first"},
        invoke=invoke,
    )
    response = Response()
    result = await cache.call(
        request=_request(),
        response=response,
        path="/api/v1/cache-test",
        cache_config={"key_builder": build_key},
        request_kwargs={"message": "second"},
        invoke=invoke,
    )

    store_key = hashlib.sha256(b"/api/v1/cache-test").hexdigest()

    assert seen_keys == [[], [store_key]]
    assert result == {"result": "ok"}
    assert response.headers[CACHE_STATUS_HEADER] == "HIT"
    assert response.headers[CACHE_KEY_HEADER] == store_key
    assert cache.metadata()[store_key].key == "/api/v1/cache-test"


@pytest.mark.asyncio
async def test_file_cache_can_be_modified(cache, monkeypatch, tmp_path):
    monkeypatch.setattr(settings.cache, "mode", "file")
    monkeypatch.setattr(settings.cache, "file_dir", str(tmp_path))

    async def invoke() -> dict[str, str]:
        return {"result": "original"}

    await cache.call(
        request=_request(),
        response=Response(),
        path="/api/v1/cache-test",
        cache_config={"key_builder": lambda _request, _context: "editable"},
        request_kwargs={},
        invoke=invoke,
    )
    cache_file = next(tmp_path.glob("*.json"))
    payload = cache_file.read_text(encoding="utf-8")
    cache_file.write_text(payload.replace("original", "edited"), encoding="utf-8")

    response = Response()
    result = await cache.call(
        request=_request(),
        response=response,
        path="/api/v1/cache-test",
        cache_config={"key_builder": lambda _request, _context: "editable"},
        request_kwargs={},
        invoke=invoke,
    )

    assert result == {"result": "edited"}
    assert response.headers[CACHE_STATUS_HEADER] == "HIT"
    assert response.headers[CACHE_KEY_HEADER] == hashlib.sha256(b"editable").hexdigest()


@pytest.mark.asyncio
async def test_max_size_removes_oldest_entry(cache, monkeypatch):
    monkeypatch.setattr(settings.cache, "max_size", 1)

    async def invoke() -> dict[str, str]:
        return {"result": "ok"}

    await cache.call(
        request=_request(path="/first"),
        response=Response(),
        path="/first",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )
    await cache.call(
        request=_request(path="/second"),
        response=Response(),
        path="/second",
        cache_config={},
        request_kwargs={},
        invoke=invoke,
    )

    assert len(cache.metadata()) == 1
    assert next(iter(cache.metadata().values())).path == "/second"
