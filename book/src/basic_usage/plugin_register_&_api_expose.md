# Plugin Register & API Expose

This chapter explains the core FrameX programming model:

1. define plugin metadata
1. register a plugin class
1. expose APIs from plugin methods

If you understand these three pieces, you understand how a capability becomes part of a FrameX service.

## Define Plugin Metadata

Each plugin module should define `__plugin_meta__` with `PluginMetadata(...)`.

Example:

```python
from framex.consts import VERSION
from framex.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A minimal example plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=["/api/v1/echo", "echo.EchoPlugin.confess"],
)
```

### Important fields

- `name`: plugin name
- `version`: plugin version
- `description`: short description of what the plugin does
- `author`: maintainer or owning team
- `url`: repo or documentation URL
- `required_remote_apis`: APIs this plugin depends on

`required_remote_apis` can contain:

- HTTP paths such as `/api/v1/echo`
- function API names such as `echo.EchoPlugin.confess`

This metadata is used for plugin discovery, dependency resolution, and runtime registration.

## Register the Plugin Class

A plugin class is registered with `@on_register()` and usually inherits from `BasePlugin`.

Example:

```python
from typing import Any

from framex.plugin import BasePlugin, on_register


@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
```

### Lifecycle guidance

- use `__init__` for lightweight synchronous setup
- use `on_start` for heavier or async initialization when needed

Example:

```python
@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    async def on_start(self) -> None: ...
```

## Expose APIs with `@on_request(...)`

Use `@on_request(...)` on plugin methods to expose them as callable APIs.

Typical modes are:

- HTTP API: provide a route path
- function API: use `call_type=ApiType.FUNC`
- both: use `call_type=ApiType.ALL`

### HTTP API example

```python
@on_request("/echo", methods=["GET"])
async def echo(self, message: str) -> str:
    return message
```

A path like `"/echo"` is exposed through the normal FrameX HTTP surface, typically as `/api/v1/echo`.

### HTTP API with request body

```python
from pydantic import BaseModel


class EchoBody(BaseModel):
    text: str


@on_request("/echo_model", methods=["POST"])
async def echo_model(self, model: EchoBody) -> dict[str, str]:
    return {"text": model.text}
```

### Function API example

```python
from framex.plugin.model import ApiType


@on_request(call_type=ApiType.FUNC)
async def confess(self, message: str) -> str:
    return f"received: {message}"
```

This creates an internal callable API. A typical function API name looks like:

```text
echo.EchoPlugin.confess
```

### Expose both HTTP and function access

```python
@on_request("/echo", methods=["GET"], call_type=ApiType.ALL)
async def echo(self, message: str) -> str:
    return message
```

Use this when the same capability should be reachable both as an HTTP route and as an internal callable API.

## Important Implementation Notes

The current implementation has a few rules worth knowing:

- a handler may declare at most one `BaseModel` parameter
- `stream=True` creates a streaming endpoint
- `raw_response=True` bypasses the default response wrapper

### Streaming example

```python
from collections.abc import AsyncGenerator


@on_request("/echo_stream", methods=["GET"], stream=True)
async def echo_stream(self, message: str) -> AsyncGenerator[str, None]:
    for chunk in [message, "done"]:
        yield chunk
```

### Raw response example

```python
@on_request("/healthz", methods=["GET"], raw_response=True)
async def healthz(self) -> dict[str, str]:
    return {"status": "ok"}
```

Without `raw_response=True`, normal non-streaming HTTP responses are wrapped by FrameX into the standard response envelope.

## Minimal End-to-End Example

```python
from typing import Any

from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.plugin.model import ApiType

__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A minimal example plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


class EchoBody(BaseModel):
    text: str


@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return message

    @on_request("/echo_model", methods=["POST"])
    async def echo_model(self, model: EchoBody) -> dict[str, str]:
        return {"text": model.text}

    @on_request(call_type=ApiType.FUNC)
    async def confess(self, message: str) -> str:
        return f"received: {message}"
```

This plugin exposes:

- HTTP `GET /api/v1/echo`
- HTTP `POST /api/v1/echo_model`
- function API `foo.FooPlugin.confess`

## Rule of Thumb

Keep this mental model:

- `PluginMetadata` describes the capability
- `@on_register()` makes the class a runtime plugin
- `@on_request(...)` turns methods into FrameX APIs

That is the core contract for building plugins in FrameX.
