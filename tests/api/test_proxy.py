from fastapi.testclient import TestClient

from framex.consts import API_STR


def test_get_proxy_version(client: TestClient):
    res = client.get(f"{API_STR}/proxy/mock/info").json()
    assert res == {"info": "i_am_mock_proxy_info"}


def test_get_proxy_get(client: TestClient):
    params = {"message": "hello world"}
    res = client.get("/proxy/mock/get", params=params).json()
    assert res == {"method": "GET", "params": params}


def test_get_proxy_post(client: TestClient):
    params = {"message": "hello world"}
    res = client.post("/proxy/mock/post", params=params).json()
    assert res == {"method": "POST", "params": params}


def test_get_proxy_post_model(client: TestClient):
    data = {"id": 12345, "name": "01234567890"}
    res = client.post("/proxy/mock/post_model", json=data).json()
    assert res == {"method": "POST", "body": data}


def test_get_proxy_black_get(client: TestClient):
    res = client.get("/proxy/mock/black_get").json()
    assert res["status"] == 404


def test_get_proxy_auth_get(client: TestClient):
    params = {"message": "hello world"}
    res = client.get("/proxy/mock/auth/get", params=params).json()
    assert res == {"method": "GET", "params": params}


def test_get_proxy_auth_sget(client: TestClient):
    params = {"message": "hello world"}
    res = client.get("/proxy/mock/auth/sget", params=params).json()
    assert res == {"method": "GET", "params": params}
