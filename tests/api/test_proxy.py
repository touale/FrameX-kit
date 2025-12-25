import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from framex.utils import cache_decode, cache_encode
from tests.test_plugins import ExchangeModel, SubModel


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


@pytest.mark.order(2)
def test_call_proxy_func(client: TestClient):
    func = cache_encode("tests.test_plugins.local_exchange_key_value")
    data = cache_encode(
        {
            "a_str": "test",
            "b_int": 123,
            "c_model": ExchangeModel(id="id_1", name=100, model=SubModel(id=1, name="sub_name")),
        }
    )
    body = {"func_name": func, "data": data}
    headers = {"Authorization": "i_am_local_proxy_auth_keys"}
    res = client.post("/api/v1/proxy/remote", json=body, headers=headers).json()
    res = cache_decode(res)
    assert res["a_str"] == "test"
    assert res["b_int"] == 123
    model = res["c_model"]
    assert model.id == "id_1"
    assert model.name == 100
    assert model.model.id == 1
    assert model.model.name == "sub_name"
