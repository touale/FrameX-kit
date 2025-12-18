import json

from fastapi.testclient import TestClient

from framex.consts import API_STR


def test_echo(client: TestClient):
    params = {"message": "hello world"}
    headers = {"Authorization": "i_am_general_auth_keys"}
    res = client.get(f"{API_STR}/echo", params=params, headers=headers).json()
    assert res["status"] == 200
    assert res["data"] == params["message"]


def test_echo_with_no_api_key(client: TestClient):
    params = {"message": "hello world"}
    res = client.get(f"{API_STR}/echo", params=params).json()
    assert res["status"] == 403
    assert res["message"] == "Not authenticated"


def test_echo_with_error_api_key(client: TestClient):
    params = {"message": "hello world"}
    headers = {"Authorization": "error_key"}
    res = client.get(url=f"{API_STR}/echo", params=params, headers=headers).json()
    assert res["status"] == 401
    assert res["message"] == "Invalid API Key(error_key) for API(/api/v1/echo)"


def test_echo_model(client: TestClient):
    params = {"message": "hello world"}
    data = {"id": 1, "name": "原神"}
    res = client.post(f"{API_STR}/echo_model", params=params, json=data).json()
    assert res["status"] == 200
    assert res["data"] == "hello world,{'id': 1, 'name': '原神'}"


def test_echo_stream(client: TestClient):
    params = {"message": "hello world"}
    with client.stream("GET", f"{API_STR}/echo_stream", params=params) as res:
        assert res.status_code == 200
        chunks = []
        events = set()

        for line in res.iter_lines():
            if line:
                if line.startswith("event: "):
                    events.add(line.removeprefix("event: "))
                elif line.startswith("data: "):
                    js = json.loads(line.removeprefix("data: "))
                    if content := js.get("content"):
                        chunks.append(content)

        assert events == {"finish", "message_chunk"}
        assert "".join(chunks) == f"原神真好玩呀, {params['message']}"
