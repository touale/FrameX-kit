import hashlib
import json
import time
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, Literal

from aiocache import Cache
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import Response

from framex.config import settings
from framex.consts import (
    CACHE_KEY_HEADER,
    CACHE_REQUEST_HEADER,
    CACHE_STATUS_HEADER,
    SUPPORTED_CACHE_METHODS,
    CacheAction,
    CacheStatus,
)
from framex.log import logger

CacheStore = Literal["memory", "file"]


class CacheEntryMetadata(BaseModel):
    key: str
    store_key: str
    store: CacheStore
    created_at: float
    expires_at: float
    ttl: int = Field(gt=0)
    path: str
    method: str


class CacheContext:
    def __init__(self, metadata: Mapping[str, CacheEntryMetadata]) -> None:
        self._metadata: Mapping[str, CacheEntryMetadata] = metadata

    def keys(self) -> list[str]:
        return list(self._metadata)

    def metadata(self) -> dict[str, CacheEntryMetadata]:
        return dict(self._metadata)

    def get_metadata(self, key: str) -> CacheEntryMetadata | None:
        return self._metadata.get(key)


class RequestCache:
    def __init__(self) -> None:
        self._memory: Cache | None = None
        self._memory_metadata: dict[str, CacheEntryMetadata] = {}

    async def call(
        self,
        *,
        request: Request,
        response: Response,
        path: str,
        cache_config: dict[str, Any] | None,
        request_kwargs: dict[str, Any],
        invoke: Callable[[], Awaitable[Any]],
    ) -> Any:
        if cache_config is None:
            response.headers[CACHE_STATUS_HEADER] = CacheStatus.BYPASS
            return await invoke()
        if not settings.cache.enabled:
            response.headers[CACHE_STATUS_HEADER] = CacheStatus.DISABLED
            return await invoke()
        if request.method.upper() not in SUPPORTED_CACHE_METHODS:
            response.headers[CACHE_STATUS_HEADER] = CacheStatus.BYPASS
            return await invoke()

        try:
            await self.cleanup()
            ttl = _resolve_ttl(cache_config)
            metadata = self.metadata()
            key = _build_cache_key(request, path, request_kwargs, cache_config, metadata)
            store_key = _hash_key(key)
            response.headers[CACHE_KEY_HEADER] = store_key
        except Exception as exc:
            logger.warning(f"Failed to prepare request cache for {request.method} {path}: {exc}")
            response.headers[CACHE_STATUS_HEADER] = CacheStatus.BYPASS
            return await invoke()

        action = _cache_action(request)

        if action == CacheAction.BYPASS:
            response.headers[CACHE_STATUS_HEADER] = CacheStatus.BYPASS
            return await invoke()
        if action == CacheAction.USE:
            try:
                cached_value = await self.get(store_key)
                if cached_value is not None:
                    response.headers[CACHE_STATUS_HEADER] = CacheStatus.HIT
                    return cached_value
            except Exception as exc:
                logger.warning(f"Failed to read request cache key {key!r}: {exc}")
                response.headers[CACHE_STATUS_HEADER] = CacheStatus.BYPASS
                return await invoke()

        result = await invoke()
        entry_metadata = CacheEntryMetadata(
            key=key,
            store_key=store_key,
            store=settings.cache.mode,
            created_at=time.time(),
            expires_at=time.time() + ttl,
            ttl=ttl,
            path=path,
            method=request.method.upper(),
        )
        try:
            await self.set(store_key, _cache_value(result), entry_metadata)
        except Exception as exc:
            logger.warning(f"Failed to write request cache key {key!r}: {exc}")

        response.headers[CACHE_STATUS_HEADER] = (
            CacheStatus.REFRESH if action == CacheAction.REFRESH else CacheStatus.MISS
        )
        return result

    def metadata(self) -> dict[str, CacheEntryMetadata]:
        if settings.cache.mode == "file":
            return self._file_metadata()
        self._drop_expired_memory()
        return dict(self._memory_metadata)

    async def get(self, store_key: str) -> Any:
        if settings.cache.mode == "file":
            return self._file_get(store_key)
        self._drop_expired_memory()
        return await self._memory_cache.get(store_key)

    async def set(self, store_key: str, value: Any, metadata: CacheEntryMetadata) -> bool:
        if settings.cache.mode == "file":
            return self._file_set(store_key, value, metadata)
        await self._memory_cache.set(store_key, value, ttl=metadata.ttl)
        self._memory_metadata[store_key] = metadata
        await self.cleanup()
        return True

    async def cleanup(self) -> None:
        if settings.cache.mode == "file":
            self._file_cleanup()
            return
        self._drop_expired_memory()
        while len(self._memory_metadata) > settings.cache.max_size:
            oldest_key = min(self._memory_metadata, key=lambda key: self._memory_metadata[key].created_at)
            await self._memory_cache.delete(oldest_key)
            self._memory_metadata.pop(oldest_key, None)

    async def clear(self) -> None:
        if self._memory is not None:
            await self._memory.clear()
        self._memory_metadata.clear()
        for path in self._file_dir().glob("*.json"):
            path.unlink(missing_ok=True)

    @property
    def _memory_cache(self) -> Cache:
        if self._memory is None:
            self._memory = Cache(Cache.MEMORY, namespace="framex-request-cache")
        return self._memory

    def _drop_expired_memory(self) -> None:
        now = time.time()
        for key, metadata in list(self._memory_metadata.items()):
            if metadata.expires_at <= now:
                self._memory_metadata.pop(key, None)

    def _file_get(self, store_key: str) -> Any:
        self._file_cleanup()
        entry = self._read_file(self._file_path(store_key))
        if not entry:
            return None
        return entry["value"]

    def _file_set(self, store_key: str, value: Any, metadata: CacheEntryMetadata) -> bool:
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            logger.warning(f"Cache value for key {metadata.key!r} is not JSON serializable; skip file cache write.")
            return False
        self._file_dir().mkdir(parents=True, exist_ok=True)
        self._file_path(store_key).write_text(
            json.dumps({"metadata": metadata.model_dump(), "value": value}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._file_cleanup()
        return True

    def _file_metadata(self) -> dict[str, CacheEntryMetadata]:
        self._file_cleanup()
        metadata: dict[str, CacheEntryMetadata] = {}
        for path in self._file_dir().glob("*.json"):
            entry = self._read_file(path)
            if entry:
                metadata[entry["metadata"].key] = entry["metadata"]
        return metadata

    def _file_cleanup(self) -> None:
        now = time.time()
        entries: list[tuple[Path, CacheEntryMetadata]] = []
        for path in self._file_dir().glob("*.json"):
            entry = self._read_file(path)
            if not entry or entry["metadata"].expires_at <= now:
                path.unlink(missing_ok=True)
                continue
            entries.append((path, entry["metadata"]))
        entries.sort(key=lambda item: item[1].created_at)
        for path, _metadata in entries[: max(0, len(entries) - settings.cache.max_size)]:
            path.unlink(missing_ok=True)

    def _read_file(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            metadata = CacheEntryMetadata.model_validate(payload["metadata"])
            return {"metadata": metadata, "value": payload.get("value")}
        except (OSError, TypeError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(f"Failed to read cache file {path}: {exc}")
            return None

    def _file_path(self, store_key: str) -> Path:
        return self._file_dir() / f"{store_key}.json"

    def _file_dir(self) -> Path:
        return Path(settings.cache.file_dir)


request_cache = RequestCache()


def normalize_cache_config(cache_config: dict[str, Any] | None) -> dict[str, Any] | None:
    if cache_config is None:
        return None
    if not isinstance(cache_config, dict):
        raise TypeError("@on_request cache must be a dict when provided")
    normalized = dict(cache_config)
    if "ttl" in normalized:
        _validate_ttl(normalized["ttl"])
    if (key_builder := normalized.get("key_builder")) and not callable(key_builder):
        raise TypeError("@on_request cache['key_builder'] must be callable")
    return normalized


def _resolve_ttl(cache_config: dict[str, Any]) -> int:
    return _validate_ttl(cache_config.get("ttl", settings.cache.ttl))


def _validate_ttl(ttl: Any) -> int:
    if not isinstance(ttl, int) or isinstance(ttl, bool) or ttl <= 0:
        raise ValueError("cache ttl must be a positive integer")
    return ttl


def _cache_action(request: Request) -> CacheAction:
    try:
        return CacheAction(request.headers.get(CACHE_REQUEST_HEADER, CacheAction.USE).strip().lower())
    except ValueError:
        return CacheAction.USE


def _build_cache_key(
    request: Request,
    path: str,
    request_kwargs: dict[str, Any],
    cache_config: dict[str, Any],
    metadata: Mapping[str, CacheEntryMetadata],
) -> str:
    if key_builder := cache_config.get("key_builder"):
        key = key_builder(request, CacheContext(metadata))
    else:
        key = json.dumps(
            {
                "method": request.method.upper(),
                "path": path,
                "kwargs": _stable_value(request_kwargs),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    if not isinstance(key, str) or not key:
        raise ValueError("cache key must be a non-empty string")
    return key


def _stable_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _stable_value(value.model_dump(mode="json", by_alias=True))
    if isinstance(value, Mapping):
        return {str(key): _stable_value(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, set):
        return [_stable_value(item) for item in sorted(value, key=repr)]
    if isinstance(value, (list, tuple)):
        return [_stable_value(item) for item in value]
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def _cache_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    return value


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
