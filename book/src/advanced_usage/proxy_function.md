# Proxy Function & Remote Invocation

This feature is for one specific case: a function may run locally in one deployment, but must run on another FrameX service in another deployment.

FrameX lets you keep the same function call in code and decide through configuration whether that function runs locally or remotely.

## When To Use It

Use proxy functions when a capability cannot or should not run in the local service.

Typical scenarios:

- the local service does not have MySQL or Redis access, but another FrameX service does
- the local service is restricted to outbound HTTP only, while another FrameX service can access internal networks
- sensitive logic should stay on the team-owned service instead of being copied into another codebase
- one team wants to call another team's internal capability without importing that implementation locally

In these cases, proxy functions let you keep the local call path stable while moving the real execution to another FrameX instance.

## How It Differs From `@on_request(...)`

Use `@on_request(...)` when you want to expose an API route.

Use `@on_proxy()` when you want a function call to stay internal, but be able to run either:

- locally
- or on a remote FrameX service

The key difference is that proxy functions are configuration-driven.

The same function can:

- run locally if it is not listed in `plugins.proxy.proxy_functions`
- run remotely if it is listed there

That switch does not require changing the call site.

## Minimal Example

```python
from typing import Any

from framex.plugin import BasePlugin, on_proxy, on_register, register_proxy_func


@on_proxy()
async def build_report(job_id: str) -> dict[str, Any]:
    return {"job_id": job_id, "status": "done"}


@on_register()
class ReportPlugin(BasePlugin):
    async def on_start(self) -> None:
        await register_proxy_func(build_report)
```

## How To Configure It

Enable the built-in `proxy` plugin and declare the remote function under `plugins.proxy.proxy_functions`.

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy.proxy_urls."http://remote-framex:8080"]
enable = ["/api/v1/*"]
disable = []

[plugins.proxy]
proxy_functions = { "http://remote-framex:8080" = ["your_module.build_report"] }
```

With this config:

- `build_report(...)` stays the same in code
- if the function name is listed in `proxy_functions`, FrameX forwards it to the remote service
- if it is not listed there, the function runs locally

## Requirements

- `@on_proxy()` only supports async functions
- proxy-function calls only support keyword arguments
- `server.enable_proxy = true` and `load_builtin_plugins = ["proxy"]` must both be set
- every URL used in `proxy_functions` must also exist in `proxy_urls`
- the remote service must also register the same proxy function during startup

## Protected Remote Services

If the remote FrameX service protects the proxy-function endpoint, add an auth rule for `/api/v1/proxy/remote` under `plugins.proxy.auth.rules`.

```toml
[plugins.proxy.auth]
rules = {
  "/api/v1/proxy/remote" = ["proxy-key"]
}
```

For the full auth model, see [Security & Authorization](./authentication.md).

## Rule Of Thumb

Use `@on_request(...)` for public API routes.

Use `@on_proxy()` when you want the same internal function call to be able to run locally or on another FrameX service, depending on configuration.
