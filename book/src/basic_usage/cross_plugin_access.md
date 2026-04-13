# Cross-Plugin Access

Cross-plugin access is how one FrameX capability calls another through a stable service interface.

This matters when:

- one plugin composes another capability
- multiple teams expose capabilities to each other
- callers should depend on APIs, not on another team's codebase
- part of the dependency graph may later move behind proxy mode

The model is simple:

1. declare what your plugin depends on
1. call those APIs through `call_plugin_api(...)`

## Declare Dependencies with `required_remote_apis`

A plugin should declare the APIs it depends on in `PluginMetadata.required_remote_apis`.

Example:

```python
__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="Calls APIs from another plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        "/api/v1/echo",
        "/api/v1/echo_model",
        "/api/v1/echo_stream",
        "echo.EchoPlugin.confess",
    ],
)
```

`required_remote_apis` can contain:

- HTTP paths such as `/api/v1/echo`
- function API names such as `echo.EchoPlugin.confess`

This declaration gives FrameX a stable contract for dependency resolution.

## Call Dependencies with `call_plugin_api(...)`

Use `call_plugin_api(api_name, **kwargs)` to call another registered API.

Example:

```python
from framex import call_plugin_api

result = await call_plugin_api("/api/v1/echo", message="hello")
```

FrameX resolves the target from `required_remote_apis`. If proxy mode is enabled, unresolved HTTP paths can fall back to the built-in `proxy` plugin.

Plugin classes also have an internal convenience wrapper around the same mechanism, but `call_plugin_api(...)` is the public API this guide uses.

## Which API Name Should You Use?

Use an HTTP path when the target capability is naturally exposed as a route:

- `/api/v1/echo`
- `/api/v1/echo_model`
- `/api/v1/echo_stream`

Use a function API name when the target capability is internal-only and should not be exposed as a public HTTP route:

- `echo.EchoPlugin.confess`

A simple rule:

- use HTTP paths for normal service-facing capabilities
- use function APIs for internal capability-to-capability calls

## Common Calling Patterns

### Call an HTTP API with simple parameters

Provider:

```python
@on_request("/echo", methods=["GET"])
async def echo(self, message: str) -> str:
    return message
```

Caller:

```python
from framex import call_plugin_api

result = await call_plugin_api("/api/v1/echo", message=message)
```

### Call an HTTP API with a model payload

Provider:

```python
class EchoBody(BaseModel):
    text: str


@on_request("/echo_model", methods=["POST"])
async def echo_model(self, model: EchoBody) -> dict[str, str]:
    return {"text": model.text}
```

Caller:

```python
from framex import call_plugin_api

result = await call_plugin_api(
    "/api/v1/echo_model",
    model={"text": "hello"},
)
```

For model payloads, pass a `dict`.

### Call a streaming API

Provider:

```python
@on_request("/echo_stream", methods=["GET"], stream=True)
async def echo_stream(self, message: str) -> AsyncGenerator[str, None]: ...
```

Caller:

```python
from framex import call_plugin_api

stream = await call_plugin_api("/api/v1/echo_stream", message=message)
```

### Call a function API

Provider:

```python
@on_request(call_type=ApiType.FUNC)
async def confess(self, message: str) -> str:
    return f"received: {message}"
```

Caller:

```python
from framex import call_plugin_api

result = await call_plugin_api("echo.EchoPlugin.confess", message=message)
```

## How to Discover Available APIs

The easiest places to inspect available APIs are:

- startup logs
- `/docs`
- `/redoc`
- `/api/v1/openapi.json`

Typical startup logs include entries like:

```text
[SUCCESS] ... Found plugin HTTP API "/api/v1/echo" from plugin(echo)
[SUCCESS] ... Found plugin HTTP API "/api/v1/echo_stream" from plugin(echo)
[SUCCESS] ... Found plugin FUNC API "echo.EchoPlugin.confess" from plugin(echo)
```

## Minimal End-to-End Example

```python
from typing import Any

from framex import call_plugin_api
from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="Calls APIs from another plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        "/api/v1/echo",
        "echo.EchoPlugin.confess",
        "/api/v1/echo_model",
    ],
)


@on_register()
class InvokerPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/evoke_echo", methods=["GET"])
    async def evoke(self, message: str) -> dict[str, Any]:
        echo = await call_plugin_api("/api/v1/echo", message=message)
        confess = await call_plugin_api("echo.EchoPlugin.confess", message=message)
        echo_model = await call_plugin_api(
            "/api/v1/echo_model",
            model={"text": message},
        )
        return {
            "echo": echo,
            "confess": confess,
            "echo_model": echo_model,
        }
```

## Rule of Thumb

Keep this mental model:

- `required_remote_apis` declares what your plugin depends on
- `call_plugin_api(...)` is the public calling interface
- HTTP paths are for service-facing APIs
- function API names are for internal callable APIs

That keeps cross-plugin dependencies explicit, stable, and easier to evolve.
