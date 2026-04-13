# Quick Start

This chapter shows the shortest path to running FrameX locally.

By the end, you will:

- install FrameX
- create one minimal plugin
- start the service
- call the plugin over HTTP
- understand what to read next

## Requirements

- Python `>=3.11`

## Install FrameX

Install the base package:

```bash
pip install framex-kit
```

If you plan to use Ray later, install the optional extra:

```bash
pip install "framex-kit[ray]"
```

## Create a Minimal Plugin

Create a file named `foo.py`:

```python
from typing import Any

from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A minimal example plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
)


class EchoBody(BaseModel):
    text: str


@on_register()
class FooPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/foo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return f"foo: {message}"

    @on_request("/foo_model", methods=["POST"])
    async def echo_model(self, model: EchoBody) -> dict[str, str]:
        return {"text": model.text}
```

This example exposes two plugin APIs:

- `GET /api/v1/foo`
- `POST /api/v1/foo_model`

FrameX discovers the plugin module, registers the plugin class, and mounts its APIs into one FastAPI service surface.

## Run the Service

Start FrameX from the same directory:

```bash
PYTHONPATH=. framex run --load-plugins foo
```

Important:

- `--load-plugins` is a repeatable option
- it is not a comma-separated list
- `PYTHONPATH=.` lets Python import the local `foo.py` module

You can also start with the built-in example plugin:

```bash
framex run --load-builtin-plugins echo
```

## Call the API

Call the GET endpoint:

```bash
curl "http://127.0.0.1:8080/api/v1/foo?message=hello"
```

Expected response:

```json
"foo: hello"
```

Call the POST endpoint:

```bash
curl -X POST "http://127.0.0.1:8080/api/v1/foo_model" \
  -H "Content-Type: application/json" \
  -d '{"text":"hello from post"}'
```

Expected response:

```json
{"text":"hello from post"}
```

## Open the API Docs

FrameX exposes standard FastAPI docs:

- `http://127.0.0.1:8080/docs`
- `http://127.0.0.1:8080/redoc`
- `http://127.0.0.1:8080/api/v1/openapi.json`

## What Just Happened

In this quick start, FrameX handled four things for you:

- plugin discovery from the module you loaded
- plugin registration through `@on_register()`
- HTTP API exposure through `@on_request(...)`
- unified service routing through one FastAPI ingress

That is the core development model: package a capability as a plugin, expose stable APIs, and let FrameX assemble them into one service.

## Next Steps

Read the next chapters in this order:

1. `Basic Usage / Overview`
1. `Project Structure`
1. `Plugin Register & API Expose`
1. `Cross-Plugin Access`
1. `Plugin Loading & Startup`

If you are evaluating FrameX for a larger system, focus on:

- plugin boundaries
- `call_plugin_api(...)`
- proxy-based upstream integration
- local vs Ray execution
