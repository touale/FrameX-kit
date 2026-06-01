<p align="center">
  <img src="docs/assets/framex-logo.svg" alt="FrameX logo" width="144" height="144">
</p>

<h1 align="center">FrameX</h1>

<p align="center">
  A plugin-first Python framework for building modular FastAPI services with optional Ray Serve support.
</p>

<p align="center">
  <a href="https://touale.github.io/FrameX-kit/"><img src="https://img.shields.io/badge/docs-online-0A7EA4" alt="Docs"></a>
  <a href="https://github.com/touale/FrameX-kit/actions/workflows/test.yml"><img src="https://github.com/touale/FrameX-kit/actions/workflows/test.yml/badge.svg" alt="CI"></a>
  <a href="https://app.codecov.io/gh/touale/FrameX-kit"><img src="https://codecov.io/gh/touale/FrameX-kit/branch/master/graph/badge.svg" alt="Coverage"></a>
  <a href="https://github.com/touale/FrameX-kit/releases"><img src="https://img.shields.io/github/v/release/touale/FrameX-kit" alt="Release"></a>
  <a href="https://pypi.org/project/framex-kit/"><img src="https://img.shields.io/pypi/v/framex-kit" alt="PyPI"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
</p>

## Overview

FrameX helps split a Python service into independently developed plugins while exposing one consistent HTTP and internal API surface. It is useful when a service needs clear module ownership, plugin loading, optional proxy integration, and a path from local execution to Ray-backed serving.

Core capabilities:

- plugin registration and discovery
- FastAPI route generation from plugin methods
- internal plugin API calls
- optional Ray Serve execution
- built-in example and proxy plugins
- configuration from environment variables, TOML, and `pyproject.toml`

![FrameX architecture](docs/assets/framex-architecture.svg)

## What Problem It Solves

FrameX is most useful when multiple teams need to ship capabilities in parallel, call each other through stable service interfaces, and keep implementation details private so each team can work without understanding or depending on other teams' codebases.

Use it when you need to:

- build service capabilities as plug-and-play modules
- let multiple engineers or teams ship in parallel with clearer ownership boundaries
- split a growing service into independently evolving capability units
- call other teams' capabilities without depending on their codebases
- expose local plugins and upstream APIs behind one consistent service surface
- integrate third-party or internal HTTP services with minimal client-side changes
- start with simple local execution and scale to Ray when needed
- keep the system extensible as capabilities, teams, and traffic grow

## Why FrameX Instead Of Plain FastAPI

Plain FastAPI is a good choice for a single cohesive application. FrameX is better when the real problem is not route handling, but service decomposition, team boundaries, and cross-service integration.

Compared with plain FastAPI, FrameX gives you:

- plugin boundaries for clearer ownership between capabilities and teams
- a better development model for plug-and-play modules and parallel delivery
- one consistent surface for local capabilities and upstream HTTP services
- internal callable APIs in addition to normal HTTP routes
- explicit dependency declarations between capabilities
- the ability to start locally and move to Ray-backed execution without rewriting plugin code

If you only need a small application with a stable route surface and one codebase, plain FastAPI is usually simpler.

## Installation

```bash
pip install framex-kit
```

Install Ray Serve support when needed:

```bash
pip install "framex-kit[ray]"
```

FrameX requires Python 3.11 or newer.

## Quick Start

Create a plugin module:

```python
from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A minimal FrameX plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
)


class EchoBody(BaseModel):
    text: str


@on_register()
class FooPlugin(BasePlugin):
    @on_request("/foo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return f"foo: {message}"

    @on_request("/foo_model", methods=["POST"])
    async def echo_model(self, model: EchoBody) -> dict[str, str]:
        return {"text": model.text}
```

Run the service:

```bash
PYTHONPATH=. framex run --load-plugins foo
```

Call the API:

```bash
curl "http://127.0.0.1:8080/api/v1/foo?message=hello"
```

Open the generated API docs:

- `http://127.0.0.1:8080/docs`
- `http://127.0.0.1:8080/redoc`
- `http://127.0.0.1:8080/api/v1/openapi.json`

You can also run the built-in example plugin:

```bash
framex run --load-builtin-plugins echo
```

## Calling Other Plugins

A plugin can call another plugin through FrameX instead of importing the other plugin's implementation directly. Declare the APIs it depends on in `required_remote_apis`, then call them with `self._call_remote_api(...)`.

```python
from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="consumer",
    version=VERSION,
    description="Call another FrameX plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=["/api/v1/foo"],
)


@on_register()
class ConsumerPlugin(BasePlugin):
    @on_request("/consumer", methods=["GET"])
    async def call_foo(self, message: str) -> str:
        return await self._call_remote_api("/api/v1/foo", message=message)
```

Run both plugins:

```bash
PYTHONPATH=. framex run \
  --load-plugins foo \
  --load-plugins consumer
```

Call the consumer API:

```bash
curl "http://127.0.0.1:8080/api/v1/consumer?message=hello"
```

`required_remote_apis` keeps plugin dependencies explicit. It can reference HTTP APIs such as `/api/v1/foo`, or internal function APIs such as `echo.EchoPlugin.confess` when a plugin exposes a function-only API.

## CLI

```bash
framex run --host 0.0.0.0 --port 8080 --load-builtin-plugins echo
```

Common options:

- `--host`
- `--port`
- `--load-plugins`
- `--load-builtin-plugins`
- `--use-ray / --no-use-ray`
- `--enable-proxy / --no-enable-proxy`
- `--dashboard-host`
- `--dashboard-port`
- `--num-cpus`

`--load-plugins` and `--load-builtin-plugins` are repeatable options:

```bash
framex run \
  --load-builtin-plugins echo \
  --load-plugins foo \
  --load-plugins your_project.plugins.bar
```

## Use Proxy Plugin

Use the built-in `proxy` plugin when you already have an HTTP service and want FrameX to expose it as part of the same API surface without writing wrapper plugin methods.

For example, if an upstream service runs at `http://127.0.0.1:9000` and exposes `GET /api/v1/chat`, FrameX can expose the same route at `http://127.0.0.1:8080/api/v1/chat` and forward matching requests to the upstream service.

Minimal configuration:

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy]
timeout = 600

[plugins.proxy.proxy_urls."http://127.0.0.1:9000"]
enable = ["/*"]
disable = []
```

Start from the CLI:

```bash
framex run --load-builtin-plugins proxy --enable-proxy
```

Common uses:

- bridge an existing FastAPI/OpenAPI service into FrameX
- expose remote team services under one gateway
- migrate APIs into plugins gradually instead of rewriting them all at once
- forward query parameters, JSON bodies, multipart forms, file uploads, and configured streaming endpoints

## Configuration

FrameX reads settings from environment variables, `.env`, `.env.prod`, `config.toml`, and `[tool.framex]` in `pyproject.toml`.

Minimal `config.toml`:

```toml
load_builtin_plugins = ["echo"]
load_plugins = ["your_project.plugins.foo"]

[server]
host = "127.0.0.1"
port = 8080
use_ray = false
enable_proxy = false

[plugins.foo]
debug = true
```

Nested environment variables are supported:

```bash
export SERVER__PORT=9000
export SERVER__ENABLE_PROXY=true
```

## Documentation

See the [online documentation](https://touale.github.io/FrameX-kit/) for plugin APIs, proxy mode, Ray mode, authentication, and advanced configuration.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).
