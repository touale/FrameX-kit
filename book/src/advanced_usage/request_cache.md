# Request Caching

FrameX can cache selected `GET` and `POST` plugin routes.

Caching has two gates:

1. enable the global cache
1. opt individual routes in with `cache={...}`

## Enable Caching

Configure the global cache in `config.toml`:

```toml
[cache]
enabled = true
mode = "memory"
ttl = 60
max_size = 1000
file_dir = ".framex/cache"
```

Fields:

- `enabled`: global cache switch
- `mode`: `memory` or `file`
- `ttl`: default lifetime in seconds; use `-1` for no expiration
- `max_size`: maximum number of entries
- `file_dir`: directory used by file mode

## Opt A Route In

Add a `cache` mapping to `@on_request(...)`:

```python
@on_request("/report", methods=["POST"], cache={"ttl": 300})
async def report(self, project_id: str) -> dict[str, str]:
    return {"project_id": project_id}
```

Use an empty mapping to inherit the global TTL:

```python
@on_request("/status", methods=["GET"], cache={})
async def status(self) -> dict[str, str]:
    return {"status": "ok"}
```

Routes without `cache={...}` bypass the cache even when `cache.enabled = true`.

## Cache Keys

By default, FrameX builds a stable key from:

- HTTP method
- route path
- handler arguments

You can provide a callable `key_builder` when a route needs a different key:

```python
from typing import Any

from starlette.requests import Request


def build_report_key(
    request: Request, context: Any, request_kwargs: dict[str, Any]
) -> str:
    return f"{request.url.path}:{request_kwargs['project_id']}"


@on_request("/report", methods=["POST"], cache={"key_builder": build_report_key})
async def report(self, project_id: str) -> dict[str, str]:
    return {"project_id": project_id}
```

The callable receives the request, a cache context, and optionally `request_kwargs`. The context exposes existing keys and metadata.

## Request Controls

Clients can control cache behavior with:

```text
X-FrameX-Cache: use
X-FrameX-Cache: bypass
X-FrameX-Cache: refresh
```

- `use`: use a cached value when present; this is the default
- `bypass`: skip cache reads and writes for this request
- `refresh`: invoke the handler and overwrite the cached value

## Response Headers

Cache-aware responses expose:

```text
X-FrameX-Cache-Key
X-FrameX-Cache-Status
```

Possible status values are:

- `DISABLED`
- `BYPASS`
- `HIT`
- `MISS`
- `REFRESH`

## Memory And File Modes

Use `memory` for a simple process-local cache.

Use `file` when cache entries should live under `cache.file_dir`. File mode writes JSON files, so cached values must be JSON serializable.

Both modes clean up expired entries and remove the oldest entries when `max_size` is exceeded.
