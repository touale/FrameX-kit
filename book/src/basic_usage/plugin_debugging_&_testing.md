# Plugin Debugging & Testing

Debugging FrameX plugins is straightforward. When **Ray is disabled** (`[server].use_ray = false`), your plugin code runs in a standard FastAPI app, so you can set breakpoints and debug just like any regular Python service.

______________________________________________________________________

## 1) Debugging

1. Disable Ray in your config.toml:

```toml
[server]
use_ray = false
```

2. Start the app normally (e.g., framex.run()).
1. Use your IDE’s debugger to set breakpoints anywhere in your plugin handlers (@on_request) or lifecycle hooks (__init__, on_start).

> With Ray disabled, there’s no difference from debugging a standard FastAPI application.

## 2) Testing

FrameX integrates naturally with pytest and fastapi.testclient. You can run the app in test mode and exercise your plugin’s HTTP endpoints and streaming behavior.

### Pytest Fixtures(`consts.py`)

```
import pytest
from typing import Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient
import framex

@pytest.fixture(scope="session", autouse=True)
def test_app() -> FastAPI:
    # Boot the FrameX app in test mode (no Ray, in-memory app)
    return framex.run(test_mode=True)  # type: ignore[return-value]

@pytest.fixture(scope="session")
def client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(test_app) as c:
        yield c
```

### Example Tests

```
import json
from fastapi.testclient import TestClient
from framex.consts import API_STR

def test_echo(client: TestClient):
    params = {"message": "hello world"}
    res = client.get(f"{API_STR}/echo", params=params).json()
    assert res["status"] == 200
    assert res["data"] == params["message"]

def test_echo_model(client: TestClient):
    params = {"message": "hello world"}
    data = {"id": 1, "name": "原神"}
    res = client.post(f"{API_STR}/echo_model", params=params, json=data).json()
    assert res["status"] == 200
    assert res["data"] == "hello world,{'id': 1, 'name': '原神'}"

def test_echo_stream(client: TestClient):
    params = {"message": "hello world"}
    # Server-Sent Events (SSE) style stream
    with client.stream("GET", f"{API_STR}/echo_stream", params=params) as res:
        assert res.status_code == 200
        chunks = []
        events = set()

        for line in res.iter_lines():
            if not line:
                continue
            if line.startswith("event: "):
                events.add(line.removeprefix("event: "))
            elif line.startswith("data: "):
                js = json.loads(line.removeprefix("data: "))
                content = js.get("content")
                if content:
                    chunks.append(content)

        assert events == {"finish", "message_chunk"}
        assert "".join(chunks) == f"原神真好玩呀, {params['message']}"
```
