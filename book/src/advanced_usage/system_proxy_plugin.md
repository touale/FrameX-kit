# System Proxy Plugin

The built-in `proxy` plugin has two core roles in FrameX, plus one more advanced extension point.

## Core Role 1: Add Upstream Services To Your Own API Surface

If you already have an upstream FastAPI service or another FrameX service, the `proxy` plugin can pull that service into the current FrameX API surface.

That means callers can keep using the current FrameX service, while some capabilities are actually forwarded to another service behind the scenes.

Typical uses:

- keep an existing FastAPI service while introducing FrameX gradually
- aggregate multiple services behind one FrameX boundary
- expose upstream APIs through the same `/api/v1/...` style surface as local plugins

### Minimal Config

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy]
white_list = ["/*"]
force_stream_apis = ["/api/v1/chat/stream"]
timeout = 600

[plugins.proxy.proxy_urls."http://127.0.0.1:9000"]
enable = ["/api/v1/*"]
disable = []
```

This `proxy_urls` mapping is the current full config form in the codebase.

The older list form still exists in the type definition, but if you want per-upstream control, use the dict form shown above.

### How It Works

At startup, the `proxy` plugin reads the upstream `/api/v1/openapi.json` document, filters routes through the configured allow rules, and registers matching forwarding routes locally.

The current implementation supports:

- query parameters
- JSON request bodies
- `multipart/form-data`
- file uploads
- explicitly marked streaming APIs

## Core Role 2: Preserve Privacy And Isolation In Multi-Plugin Collaboration

The second role is more important in larger systems.

In a multi-plugin or multi-team setup, one team may need to call another team's capability without having that plugin code locally.

In that case, the caller only depends on the API contract, not on the other team's implementation.

This gives you two benefits:

- implementation privacy: the upstream plugin code does not need to be shared locally
- codebase isolation: one team does not need to understand or import another team's plugin package

### What This Looks Like

A plugin declares the API it depends on:

```python
__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="Calls another capability through a stable API",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=["/api/v1/base/version"],
)
```

Then it calls that API through the normal public interface:

```python
from framex import call_plugin_api

version = await call_plugin_api("/api/v1/base/version")
```

If that API exists locally, FrameX uses the local plugin.

If it does not exist locally and proxy mode is enabled, the HTTP path can fall back to the `proxy` plugin and be forwarded to an upstream service.

That is the key point: the calling side does not need to change just because the real implementation lives somewhere else.

## Proxy URL Rules

The proxy plugin supports two rule levels:

- global rules through `white_list`
- per-upstream rules through `proxy_urls.<base_url>.enable` and `proxy_urls.<base_url>.disable`

Example:

```toml
[plugins.proxy]
white_list = ["/api/v1/*"]

[plugins.proxy.proxy_urls."http://127.0.0.1:9000"]
enable = ["/api/v1/*"]
disable = ["/api/v1/internal/*"]
```

Rule order in the code is:

1. per-URL `disable`
1. per-URL `enable`
1. global `white_list`

## Streaming APIs

If an upstream route should stay on the streaming path, add it to `force_stream_apis`:

```toml
[plugins.proxy]
force_stream_apis = ["/api/v1/chat/stream"]
```

Those paths stay on the streaming code path instead of being handled as normal JSON responses.

## Authentication

If the upstream service is another FrameX service and it has enabled `auth.rules`, you need to configure matching keys in `plugins.proxy.auth.rules` so the proxy plugin can call it successfully.

The proxy plugin uses these rules in two places:

- when fetching the upstream `/api/v1/openapi.json`
- when forwarding requests to protected upstream API paths

Example:

```toml
[plugins.proxy.auth]
rules = {
  "/api/v1/openapi.json" = ["docs-key"],
  "/api/v1/base/version" = ["service-key"],
  "/api/v1/base/*" = ["service-key"]
}
```

That means:

- the proxy plugin uses `docs-key` to read the upstream OpenAPI document
- it uses `service-key` when forwarding protected API calls to `/api/v1/base/version` or `/api/v1/base/*`

So if a cloud FrameX service protects its routes with `auth.rules`, the local service must mirror the needed upstream path rules in `plugins.proxy.auth.rules` and provide the corresponding keys.

For the full auth model and rule behavior on the upstream service itself, see [Security & Authorization](./authentication.md).

## Advanced Use Cases

The `proxy` plugin also supports more advanced usage patterns beyond plain HTTP route forwarding.

One of them is function-style proxying and remote invocation. That topic is covered separately in [Proxy Function & Remote Invocation](./proxy_function.md).

## Rule Of Thumb

Use the `proxy` plugin when you need one of these outcomes:

- expose an upstream FastAPI or FrameX service through your current FrameX API surface
- let one plugin call another team's capability without importing or shipping that plugin locally
- keep API names stable while the real implementation moves between local and remote services
