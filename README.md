# FrameX

[![pipeline status](https://github.com/touale/FrameX-kit/actions/workflows/test.yml/badge.svg)](https://github.com/touale/FrameX-kit/actions/workflows/test.yml)
[![coverage report](https://codecov.io/gh/touale/FrameX-kit/branch/master/graph/badge.svg)](https://app.codecov.io/gh/touale/FrameX-kit)
[![Latest Release](https://img.shields.io/github/v/release/touale/FrameX-kit?label=latest)](https://github.com/touale/FrameX-kit/releases)

**FrameX** is a lightweight, pluggable Python framework designed for building modular and extensible algorithmic systems.\\

It provides a clean architecture that supports **dynamic plugin registration**, **isolated execution**, and **secure invocation**, making it well-suited for multi-algorithm collaboration, heterogeneous task scheduling, and distributed deployments.

Each algorithm can be developed, deployed, and loaded as an independent plugin, achieving infinite scalability.

![](./book/src/img/v2andv3.svg)

______________________________________________________________________

## Project Information

- **Author:** Touale Cula
- **License:** MIT
- **Source Code:** [FrameX Repository](https://github.com/touale/FrameX-kit)
- **Online Documentation:** [FrameX Docs](https://touale.github.io/FrameX-kit/)

______________________________________________________________________

## Key Features

- **Plugin-Based Architecture**\
  Algorithms are encapsulated as independent plugins, which can be added, removed, or updated without impacting others.
- **Distributed Execution with Ray**\
  Optional Ray integration delivers high concurrency, high throughput, and resilience against blocking tasks.
- **Cross-plugin Calls**\
  Enables interaction between local and remote plugins. If a plugin is not available locally, the system automatically routes the request to the corresponding cloud plugin.
- **Backward Compatibility**\
  FrameX can seamlessly forward requests to standard FastAPI endpoints, enabling smooth integration without code changes.
- **Streaming Support**\
  Native support for streaming responses, suitable for long-running or large-scale inference tasks.
- **Built-in Observability**\
  Integrated logging, tracing, and performance monitoring to ease debugging and root-cause analysis.
- **Flexible Configuration & Tooling**\
  Clean configuration management (`.toml`, `.env`) plus scaffolding, packaging, and CI/CD integration for automation.

## Installation

```
pip install framex-kit
```

### 1) Execute by loading your plugin

Create foo.py file

```
from typing import Any
from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request


__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A simple Foo plugin example",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
)


class FooModel(BaseModel):
    text: str = "Hello Foo"


@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/foo", methods=["GET"])
    async def foo(self, message: str) -> str:
        return f"Foo says: {message}"

    @on_request("/foo_model", methods=["POST"])
    async def foo_model(self, model: FooModel) -> str:
        return f"Foo received model: {model.text}"#   
```

Run the following command to start the project creation process:

```
$ PYTHONPATH=. framex run --load-plugins foo
🚀 Starting FrameX with configuration:
{
  "host": "127.0.0.1",
  "port": 8080,
  "dashboard_host": "127.0.0.1",
  "dashboard_port": 8260,
  "use_ray": false,
  "enable_proxy": false,
  "num_cpus": 8,
  "excluded_log_paths": []
}
11-05 16:01:13 [SUCCESS] framex.plugin.manage | Succeeded to load plugin "foo" from foo
11-05 16:01:13 [INFO] framex | Start initializing all DeploymentHandle...
11-05 16:01:13 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "['/api/v1/foo', '/api/v1/foo_model']" from plugin(foo)
11-05 16:01:13 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/foo from foo.FooPlugin
11-05 16:01:13 [SUCCESS] framex.driver.ingress | Succeeded to register api(['POST']): /api/v1/foo_model from foo.FooPlugin
INFO:     Started server process [59373]
INFO:     Waiting for application startup.
11-05 16:01:13 [INFO] framex.driver.application | Starting FastAPI application...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

### 2) Execute by loading a system plugin

```
$ framex run --load-builtin-plugins echo
🚀 Starting FrameX with configuration:
{
  "host": "127.0.0.1",
  "port": 8080,
  "dashboard_host": "127.0.0.1",
  "dashboard_port": 8260,
  "use_ray": false,
  "enable_proxy": false,
  "num_cpus": 8,
  "excluded_log_paths": []
}
11-05 16:27:36 [SUCCESS] framex.plugin.manage | Succeeded to load plugin "echo" from framex.plugins.echo
11-05 16:27:36 [INFO] framex | Start initializing all DeploymentHandle...
11-05 16:27:36 [SUCCESS] framex.plugin.manage | Found plugin HTTP API "['/api/v1/echo', '/api/v1/echo_model', '/api/v1/echo_stream']" from plugin(echo)
11-05 16:27:36 [SUCCESS] framex.plugin.manage | Found plugin FUNC API "['echo.EchoPlugin.confess']" from plugin(echo)
11-05 16:27:36 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/echo from echo.EchoPlugin
11-05 16:27:36 [SUCCESS] framex.driver.ingress | Succeeded to register api(['POST']): /api/v1/echo_model from echo.EchoPlugin
11-05 16:27:36 [SUCCESS] framex.driver.ingress | Succeeded to register api(['GET']): /api/v1/echo_stream from echo.EchoPlugin
INFO:     Started server process [554]
INFO:     Waiting for application startup.
11-05 16:27:36 [INFO] framex.driver.application | Starting FastAPI application...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

### 3) Execute by loading a third-party plugin

```
framex run --load-plugins <plugin_name>,<plugin_name>
```

## Application Scenarios

- **Quick Onboarding & Project Setup**\
  New developers can rapidly bootstrap projects and reuse existing algorithms via remote calls, without accessing legacy code.

- **Multi-Team Parallel Development & Isolation**\
  Different teams manage their own isolated plugin spaces. Access control ensure security and reduce interference.

- **Hybrid Deployment & Smooth Migration**\
  Supports hybrid calls with other FastAPI services, dynamic endpoint registration, and multi-instance FrameX deployment with inter-instance communication.

- **Modular Delivery & Commercial Licensing**\
  Deliver selected algorithm modules locally to clients while keeping others as remotely callable services. This supports licensing, pay-per-use, and flexible business models.
