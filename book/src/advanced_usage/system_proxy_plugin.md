# System Proxy Plugin: API Compatibility with Regular FastAPI Projects and Other FrameX Instances

Its goal is to support progressive adoption of FrameX — allowing any unmigrated or legacy algorithms to be automatically forwarded to external services or other FrameX instances during the transition, ensuring compatibility and service stability.

In addition, the proxy can forward cross-plugin requests across different FrameX instances, including remote instances, enabling distributed execution and transparent inter-instance communication within the same unified API interface.

______________________________________________________________________

## Why use the Proxy?

- **Gradual migration** — Maintain legacy services while progressively adopting FrameX.
- **API compatibility** — Expose existing endpoints through FrameX with minimal integration effort.
- **Zero code intrusion** — Invoke remote or legacy APIs using the same `_call_remote_api(...)` interface.
- **Streaming support** — Enable selective streaming behavior via `force_stream_apis`.

**`config.toml`**

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy]
proxy_urls = ["http://127.0.0.1:80"]
force_stream_apis = ["/api/v1/chat"]
```

The proxy automatically **discovers available APIs** (for example, through OpenAPI introspection) and dynamically **maps them to corresponding call signatures** within FrameX.

For any **streaming endpoints** defined in `force_stream_apis`, the proxy automatically handles responses as **Server-Sent Events (SSE)** or **chunked data streams**, depending on the endpoint’s behavior.

## Calling Legacy APIs from FrameX

You can easily invoke legacy APIs (e.g., from existing FastAPI services or other FrameX instances) through the System Proxy Plugin.
Simply declare the remote APIs in your plugin metadata, and call them using the \_call_remote_api(...) helper.
Basic types can be passed directly, while Pydantic models should be converted to dict form.

```
__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="Invoke external APIs via the system proxy",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        "/api/v1/base/match", # Define your dependent APIs here
    ],
)

# Simple call (non-streaming)
remote_version = await self._call_remote_api("/api/v1/base/version")

# Call with body payload (Pydantic -> dict)
match_result = await self._call_remote_api(
    "/api/v1/base/match",
    model={
        "name": "test",
    },
)
```

That’s it — the proxy automatically forwards your call to the corresponding service, adapts the request/response formats when necessary, and returns the result to your plugin seamlessly.

## Streaming Endpoints

Add any streaming paths to force_stream_apis so the proxy treats them as **streaming**:

```
[plugins.proxy]
proxy_urls = ["http://127.0.0.1:80"]
force_stream_apis = ["/api/v1/chat", "/api/v1/echo_stream"]
```

Then, when you call those endpoints via \_call_remote_api(...), you’ll receive an async iterable (or SSE lines) that you can consume incrementally in v3.

## Configuration Reference

```
[server]
enable_proxy = true      # Enable the proxy bridge

[plugins.proxy]
proxy_urls = ["http://<host>:<port>", "..."]   # One or more upstream API endpoints (supports load balancing)
force_stream_apis = ["/api/v1/chat"]           # Endpoints treated as streaming

# Optional filters:
# white_list = ["/api/v1/*"]                   # Whitelisted API paths (restricts to these only)
```

## Transparent Migration (Zero-Code Changes)

One of the key advantages of the **Proxy Plugin** design is its support for **transparent migration**:

- Once an API is declared in `required_remote_apis` and invoked through `_call_remote_api(...)`, it **does not matter** where the actual implementation resides — whether in a legacy service or another FrameX instance.
- When that implementation is later migrated into the current FrameX environment as a native plugin, the framework will **automatically route** calls to the new local version.
- Your plugin code **remains completely unchanged** — no modification to call sites or configuration is required.

This ensures a smooth transition path where business logic and integrations stay stable while the backend evolves naturally.
