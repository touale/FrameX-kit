# Plugin Register & API Expose

Every plugin **must** declare metadata and a plugin class. This section explains how to register a plugin, define its metadata, and expose APIs (HTTP, streaming, or function calls).

______________________________________________________________________

## 1) Plugin Metadata (`__plugin_meta__`)

Each plugin **must** define `__plugin_meta__ = PluginMetadata(...)`. Fill it carefully and accurately—this information is used for discovery, dependency resolution, routing, and UI/display.

Guidelines for fields:

- `name` (required): A short, unique, human-readable plugin name.
- `version` (required): Follow semantic versioning (e.g., `1.2.0`).
- `description` (required): What the plugin does and when to use it.
- `author` (required): Owner/maintainer identity (team/company).
- `url` (required): Project/repo/docs link for the plugin.
- `required_remote_apis`: A list of external API paths your plugin depends on (e.g. endpoints provided by other plugins/services). It enables dependency checks and optional preflight validation.

For example:

```
__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="原神会重复你说的话",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)
```

## 2) Plugin Class & Registration

Each plugin must implement a class decorated with `@on_register()` and inherit from `BasePlugin`.

For example:

```
@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Initialize lightweight resources here (e.g., clients, caches)

    async def on_start(self) -> None:
        # Initialize heavy/async resources here (e.g., DB connections, pools)
        # Called by the runtime when the plugin is starting.
        ...

```

Notes:

- Use `__init__` for fast, synchronous setup. (Initialization of parameter values)
- Use `on_start` for asynchronous or heavy initialization (DB, message queues, engines).

## 3) Exposing APIs with `@on_request(...)`

Annotate **methods on your plugin class** with `@on_request(...)` to expose them as callable endpoints.

Parameters:

- `path`:
  - For `ApiType.HTTP`: the URL path (e.g. `"/echo"` or `"/v1/echo"`).
  - For `ApiType.FUNC`: the symbolic name of the function. If omitted, the **method name** is used.
- `methods`: HTTP methods (e.g. `["GET"]`, `["POST"]`). For function calls, leave it as `None`.
- `call_type`: One of `ApiType.HTTP` or `ApiType.FUNC`.
- `stream`: Whether the endpoint is streaming. If `True`, the handler should be an async generator or follow the framework’s streaming contract.

### ApiType Explained

- **`ApiType.HTTP`**

  - Exposes the plugin method as an HTTP endpoint.
  - Can be consumed by external clients (e.g., web backends, mobile apps, or third-party services).
  - Can also be used for plugin-to-plugin communication.
  - Offers broader accessibility and is automatically documented under `/docs` (Swagger/OpenAPI).
  - Recommended when you want to share functionality beyond the plugin boundary.

- **`ApiType.FUNC`**

  - Exposes the plugin method as an **internal remote function**.
  - Only callable from **within the FrameX plugin ecosystem**.
  - Provides stricter scoping and reduced exposure surface.
  - Recommended for internal-only calls, utility helpers, or private APIs that should not be published externally.

### 3.1 HTTP example (non-stream)

```
__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="原神会重复你说的话",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


class EchoModel(BaseModel):
    id: int
    name: str = "原神"


@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return message
```

### 3.2 HTTP example (streaming)

```
...
@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request(path="/echo_stream", methods=["GET"], call_type=ApiType.HTTP, stream=True)
    async def echo_stream(self, message: str):
        # yield chunked events/messages
        for ch in f"Streaming: {message}":
            yield {"type": "chunk", "data": ch}
        yield {"type": "finish"}
```

### 3.3 Function call example

```
...
@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request(call_type=ApiType.FUNC)
    async def add(self, a: int, b: int) -> int:
        return a + b
```

## 4) End-to-End Example

```
# src/__init__.py

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.plugin.model import ApiType
from framex.utils import StreamEnventType, make_stream_event

__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="原神会重复你说的话",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


class EchoModel(BaseModel):
    id: int
    name: str = "原神"


@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return message

    @on_request("/echo_model", methods=["POST"])
    async def echo_model(self, message: str, model: EchoModel) -> str:
        return f"{message},{model.model_dump()}"

    @on_request("/api/v1/echo_stream", methods=["GET"], stream=True)
    async def echo_stream(self, message: str) -> AsyncGenerator[str, None]:
        for char in f"原神真好玩呀, {message}":
            yield make_stream_event(StreamEnventType.MESSAGE_CHUNK, char)
            await asyncio.sleep(0.1)
        yield make_stream_event(StreamEnventType.FINISH)

    @on_request(call_type=ApiType.FUNC)
    async def confess(self, message: str) -> str:
        return f"我是原神哟! 收到您的消息{message}"

```
