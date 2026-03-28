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


def test_get_proxy_upload(client: TestClient):
    params = {"message": "hello world"}
    data = {"note": "upload note"}
    files = {
        "ppt_file": (
            "demo.pptx",
            b"ppt-content",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        "txt_file": ("demo.txt", b"txt-content", "text/plain"),
    }
    res = client.post("/proxy/mock/upload", params=params, data=data, files=files).json()
    assert res == {
        "method": "POST",
        "params": params,
        "body": data,
        "files": [
            {
                "field": "ppt_file",
                "filename": "demo.pptx",
                "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            },
            {
                "field": "txt_file",
                "filename": "demo.txt",
                "content_type": "text/plain",
            },
        ],
    }


def test_get_proxy_upload_openapi(client: TestClient):
    data = client.get("/api/v1/openapi.json").json()
    post = data["paths"]["/proxy/mock/upload"]["post"]
    ref = post["requestBody"]["content"]["multipart/form-data"]["schema"]["$ref"].split("/")[-1]
    schema = data["components"]["schemas"][ref]
    assert schema["properties"]["ppt_file"]["format"] == "binary"
    assert schema["properties"]["txt_file"]["format"] == "binary"


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
    assert res["status"] == 200
    data = cache_decode(res["data"])
    assert data["a_str"] == "test"
    assert data["b_int"] == 123
    model = data["c_model"]
    assert model.id == "id_1"
    assert model.name == 100
    assert model.model.id == 1
    assert model.model.name == "sub_name"


@pytest.mark.order(2)
def test_call_proxy_func_with_error_func_name(client: TestClient):
    func = cache_encode("tests.test_plugins.error_func")
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
    assert res["status"] == 500


@pytest.mark.order(2)
def test_call_proxy_func_with_error_api_key(client: TestClient):
    func = cache_encode("tests.test_plugins.local_exchange_key_value")
    data = cache_encode(
        {
            "a_str": "test",
            "b_int": 123,
            "c_model": ExchangeModel(id="id_1", name=100, model=SubModel(id=1, name="sub_name")),
        }
    )
    body = {"func_name": func, "data": data}
    headers = {"Authorization": "i_am_error_keys"}
    res = client.post("/api/v1/proxy/remote", json=body, headers=headers).json()
    assert res["status"] == 401
