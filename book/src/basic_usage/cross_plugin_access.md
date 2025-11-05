# Cross-Plugin Access

FrameX allows a plugin to call APIs exposed by **other** plugins. This is useful for composition, reuse, and gradual migration across teams.

There are **two steps** to make a cross-plugin call:

1. **Declare dependencies** in `PluginMetadata.required_remote_apis`.
1. **Invoke** the remote API with `self._call_remote_api(...)` inside your plugin class.

______________________________________________________________________

## 1) Declare Required Remote APIs

Always declare what you will call in your plugin’s metadata. For example:

```python
__plugin_meta__ = PluginMetadata(
    name="my-plugin",
    version="0.1.0",
    description="Demonstrates cross-plugin access",
    author="touale",
    url="http://example.local/FrameX",
    required_remote_apis=[
        "/api/v1/echo",  # HTTP (basic types)
        "/api/v1/echo_model",  # HTTP (BaseModel payload)
        "/api/v1/echo_stream",  # HTTP streaming
        "echo.EchoPlugin.confess",  # FUNC call
    ],
)
```

## 2) Call Remote APIs with self.\_call_remote_api(...)

Use self.\_call_remote_api(api_name, \*\*kwargs) inside your plugin. The api_name is either:

- The HTTP path (e.g., "/api/v1/echo"), or
- The FUNC name (e.g., "echo.EchoPlugin.confess").

Arguments are passed as keyword arguments.

- Primitive types (str/int/float/bool) → pass directly.
- Pydantic models → pass a dict (e.g., model.model_dump() or a manually constructed dict).

### 2.1 HTTP (Basic Types)

Remote provider:

```
@on_request("/echo", methods=["GET"])
async def echo(self, message: str) -> str:
    return message
```

Caller usage:

```
result = await self._call_remote_api("/api/v1/echo", message=message)
```

### 2.2 HTTP (BaseModel Payload)

Remote provider:

```
class EchoModel(BaseModel):
    id: int
    name: str

@on_request("/echo_model", methods=["POST"])
async def echo_model(self, message: str, model: EchoModel) -> str:
    return f"{message},{model.model_dump()}"
```

Caller usage:

```
res = await self._call_remote_api(
    "/api/v1/echo_model",
    message=message,
    model={"id": 1, "name": "Genshin Impact"}  # BaseModel as dict
)
```

### 2.3 HTTP Streaming

Remote provider:

```
@on_request("/api/v1/echo_stream", methods=["GET"], stream=True)
async def echo_stream(self, message: str) -> AsyncGenerator[str, None]:
    for ch in f"Streaming fun, {message}":
        yield make_stream_event(StreamEnventType.MESSAGE_CHUNK, ch)
        await asyncio.sleep(0.1)
    yield make_stream_event(StreamEnventType.FINISH)
```

Caller usage:

```
stream = await self._call_remote_api("/api/v1/echo_stream", message=message)
stream_text = "".join([extract_content(evt) for evt in stream if "message_chunk" in evt])
```

### 2.4 FUNC Calls

```
@on_request(call_type=ApiType.FUNC)
async def confess(self, message: str) -> str:
    return f"Got your message: {message}"
```

Caller usage:

```
res = await self._call_remote_api("echo.EchoPlugin.confess", message=message)
```

## 3) How to Find api_name

An easy way to discover all available APIs is to check the startup logs, which list detected plugins and endpoints. Example:

```
09-04 15:10:54 [SUCCESS] framex.plugin.manage | Succeeded to load plugin "echo" from framex.plugins.echo
09-04 15:10:54 [INFO] framex | Start initializing all DeploymentHandle...
09-04 15:10:54 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "/api/v1/echo" from plugin(hello_world)
09-04 15:10:54 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "/api/v1/echo_stream" from plugin(hello_world)
09-04 15:10:54 [SUCCESS] framex.plugin.manage | Found plugin FUNC API "echo.EchoPlugin.confess" from plugin(echo)
```

## 4) End-to-End Example

```
import time
from typing import Any

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request, remote

__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="原神会调用远程方法哟",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        "/api/v1/echo",
        "echo.EchoPlugin.confess",
        "/api/v1/echo_stream",
        "/api/v1/echo_model",
        
        
    ],
)


@on_register()
class InvokerPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


    @on_request("/evoke_echo", methods=["GET"])
    async def evoke(self, message: str) -> list[Any]:
        def extract_content(chunk: str) -> str:
            return chunk.split('"content": "')[-1].split('"')[0]

        echo = await self._call_remote_api("/api/v1/echo", message=message)
        stream = await self._call_remote_api("/api/v1/echo_stream", message=message)
        stream_text = "".join([extract_content(c) for c in stream if "message_chunk" in c])
        confess = await self._call_remote_api("echo.EchoPlugin.confess", message=message)
        echo_model = await self._call_remote_api(
            "/api/v1/echo_model", message=message, model={"id": 1, "name": "原神"}
        )
        return [echo, stream_text, confess, echo_model]

```
