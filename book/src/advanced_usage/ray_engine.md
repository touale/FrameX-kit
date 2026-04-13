# Integrating Ray Engine

Ray is the optional distributed execution backend in FrameX.

Its role is to move the runtime from local process execution to Ray-backed execution, while keeping the same plugin model and API surface.

## Core Role

When Ray is enabled, FrameX keeps the same plugin structure but changes the execution backend.

That means:

- plugin deployments run through Ray Serve
- the main FastAPI ingress is mounted through Ray Serve
- plugin code does not need to be rewritten just because the backend changes

In other words, Ray changes how the system runs, not how plugins are written.

## Install Ray Support

Ray support is optional:

```bash
pip install "framex-kit[ray]"
```

If Ray is not installed and you enable `use_ray = true`, startup fails.

## Enable Ray

Turn it on in configuration:

```toml
[server]
use_ray = true
dashboard_host = "127.0.0.1"
dashboard_port = 8260
```

You can also set the same values through CLI options or environment variables.

## What Changes After Enabling Ray

When `server.use_ray = true`:

- FrameX switches from the local adapter to `RayAdapter`
- plugin deployments become Ray Serve deployments
- the main ingress is mounted through Ray Serve

What does not change:

- `PluginMetadata`
- `@on_register()`
- `@on_request(...)`
- `call_plugin_api(...)`
- plugin import paths and loading model

## Example Config

```toml
load_builtin_plugins = ["echo"]
load_plugins = ["your_project.plugins.foo"]

[server]
host = "127.0.0.1"
port = 8080
use_ray = true
dashboard_host = "127.0.0.1"
dashboard_port = 8260
```

## Ray Dashboard

When Ray is enabled, the dashboard is available at the configured dashboard host and port.

Example:

```toml
[server]
dashboard_host = "127.0.0.1"
dashboard_port = 8260
```

## Constraints

If your codebase uses `@remote()`, enabling Ray changes how those calls execute at runtime. The detailed behavior is covered in [Advanced Remote Calls & Non-Blocking Execution](./remote_calls.md).

## Rule Of Thumb

Use Ray when you need the same plugin model with a different execution backend.

Keep local mode when you are developing, debugging, or running lightweight tests.
