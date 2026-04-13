# Plugin Debugging & Testing

This chapter covers two practical tasks:

1. debugging plugins locally
1. testing plugins with `pytest`

## Debug Plugins Locally

For local debugging, keep Ray disabled.

`config.toml`:

```toml
[server]
use_ray = false
```

In this mode, FrameX runs as a normal FastAPI application, so you can debug it like any other Python web service.

## Keep Ray Off During Normal Debugging

If you are still changing plugin logic, keep `use_ray = false` until the behavior is stable.

Use Ray only when you specifically need to debug distributed execution behavior.

## Build a Test App

For tests, start FrameX in test mode and return the FastAPI app.

```python
import pytest
from fastapi import FastAPI

import framex


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    framex.load_builtin_plugins("echo")
    framex.load_plugins("your_project.plugins.foo")
    return framex.run(test_mode=True)  # type: ignore[return-value]
```

## Use `TestClient`

Wrap the test app with `TestClient`:

```python
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client(test_app) -> Generator[TestClient, None, None]:
    with TestClient(test_app) as test_client:
        yield test_client
```

## Example HTTP Test

```python
from fastapi.testclient import TestClient


def test_echo(client: TestClient) -> None:
    response = client.get("/api/v1/echo", params={"message": "hello"})
    assert response.status_code == 200
    assert response.json()["data"] == "hello"
```

## Test Streaming APIs

If a plugin exposes a streaming endpoint, test it with `client.stream(...)`.

```python
def test_stream(client: TestClient) -> None:
    with client.stream(
        "GET", "/api/v1/echo_stream", params={"message": "hello"}
    ) as response:
        assert response.status_code == 200
```

## Rule of Thumb

Use this simple workflow:

- debug in local mode with Ray off
- test through HTTP with `framex.run(test_mode=True)`
- turn Ray on only for dedicated integration coverage
