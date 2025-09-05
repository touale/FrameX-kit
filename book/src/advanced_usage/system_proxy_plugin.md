# System Proxy Plugin (v2 API Compatibility)

The **System Proxy Plugin** enables seamless **backward compatibility** with your existing v2 services.\
Its goal is to provide **progressive adoption** of v3: any **unmigrated** algorithms can be **automatically forwarded** to v2 during the transition period, ensuring **compatibility** and **service stability**.

______________________________________________________________________

## Why use the Proxy?

- **Gradual migration**: keep v2 running while you onboard to v3.
- **API parity**: expose v2 endpoints through v3 with minimal effort.
- **Zero invasive changes**: call v2 via the same `_call_remote_api(...)` interface.
- **Streaming support**: selective streaming via `force_stream_apis`.

**`config.toml`**

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy]
proxy_urls = ["http://127.0.0.1:80"]
force_stream_apis = ["/api/v1/chat"]
```

The proxy will auto-discover v2 APIs (e.g., via its OpenAPI/inspection) and map them to v3 call signatures.

For streaming endpoints listed in force_stream_apis, v3 will treat responses as server-sent events (SSE) or chunked streams accordingly.

## Calling v2 from v3

Declare v2 apis in your plugin metadata, then call them with \_call_remote_api(...).
Basic types can be passed directly; **Pydantic models** must be passed as dicts.

```
__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="Invoke v2 APIs via the system proxy",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        
        
    ],
)

# Simple call (non-streaming)
remote_version = await self._call_remote_api("/api/v1/base/version")

# Call with body model (dict form)
match_result = await self._call_remote_api(
    
    model={
        
        
    },
)
```

That’s it — the proxy will forward your call to v2, adapt request/response shapes where applicable, and return results to v3 callers.

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
enable_proxy = true      # turn on the proxy bridge

[plugins.proxy]
proxy_urls = ["http://<v2-host>:<port>", "..."]  # one or more v2 base URLs (load-balanced/round-robin)
force_stream_apis = ["/api/v1/chat"]             # endpoints treated as streaming
# optional:
# black_list = ["/api/v1/admin/*"]               # deny-list
# white_list = ["/api/v1/*"]                     # allow-list (if present, only these paths are allowed)
```

## Transparent Migration (No-Code Changes)

One of the biggest advantages of the `proxy plugin` design is transparent migration:

- As long as you declare the API in required_remote_apis and call it via \_call_remote_api(...), it **does not matter** whether the implementation lives in v2 or v3.
- When a v2 algorithm is later migrated into v3 (rewritten as a v3 plugin), the framework will **automatically** route calls to the new v3 implementation.
- Your plugin code **remains unchanged** — you don’t need to touch any call sites.

This ensures a smooth transition where business logic and integrations remain stable while the backend evolves.
