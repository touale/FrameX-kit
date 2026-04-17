import asyncio

import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from framex.driver.auth import create_auth_session, create_jwt
from framex.utils import cache_decode, cache_encode
from tests.test_plugins import ExchangeModel, SubModel, local_exchange_key_value


def _set_oauth_session(client: TestClient, monkeypatch) -> None:
    from framex.config import settings

    oauth = type(
        "OAuthConfig",
        (),
        {
            "provider": "gitlab",
            "jwt_secret": "test-secret-test-secret-test-secret",
            "jwt_algorithm": "HS256",
            "authorization_url": "https://oauth.example.com/authorize",
            "client_id": "client",
            "call_back_url": "http://test/callback",
        },
    )()
    monkeypatch.setattr(settings.auth, "oauth", oauth)

    session_id = create_auth_session(
        {
            "username": "tester",
            "oauth_provider": "gitlab",
            "oauth_access_token": "oauth-token",
        }
    )
    token = create_jwt(
        {
            "username": "tester",
            "oauth_provider": "gitlab",
            "session_id": session_id,
        }
    )
    client.cookies.set("framex_token", token)


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


def test_openapi_tag_description_shows_lazy_release_view(client: TestClient, monkeypatch):
    from framex.config import settings

    monkeypatch.setattr(settings.auth, "oauth", None)
    data = client.get("/api/v1/openapi.json").json()

    descriptions = [tag.get("description") or "" for tag in data.get("tags", [])]
    assert any("/docs/plugin-release?plugin=proxy" in description for description in descriptions)


def test_openapi_tag_description_hides_plugin_config_without_auth(client: TestClient, monkeypatch):
    from framex.config import settings

    monkeypatch.setattr(settings.auth, "oauth", None)
    data = client.get("/api/v1/openapi.json").json()

    descriptions = [tag.get("description") or "" for tag in data.get("tags", [])]
    assert all("View Config" not in description for description in descriptions)
    assert all("/docs/plugin-config?plugin=proxy" not in description for description in descriptions)


def test_get_plugin_release_documentation(client: TestClient, monkeypatch):
    async def fake_get_latest_repository_version(_: str) -> str:
        return "v9.9.9"

    monkeypatch.setattr("framex.driver.application.get_latest_repository_version", fake_get_latest_repository_version)

    response = client.get("/docs/plugin-release", params={"plugin": "proxy"})

    assert response.status_code == 200
    assert response.json() == {
        "has_update": True,
        "latest_version": "v9.9.9",
        "repo_url": "https://github.com/touale/FrameX-kit",
    }


def test_get_plugin_config_documentation_requires_auth(client: TestClient, monkeypatch):
    from framex.config import settings

    monkeypatch.setattr(settings.auth, "oauth", None)
    response = client.get("/docs/plugin-config", params={"plugin": "proxy"})

    assert response.status_code == 403
    assert response.json()["message"] == "Plugin config documentation requires auth"


def test_get_plugin_config_documentation_rejects_settings_only_config(client: TestClient, tmp_path, monkeypatch):
    from framex.config import settings

    _set_oauth_session(client, monkeypatch)
    yaml_path = tmp_path / "proxy-extra.yaml"
    yaml_path.write_text(
        "token: embedded-secret\nnested:\n  client_secret: inner-secret\nname: proxy\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings.docs, "embedded_config_file_whitelist", ["proxy-extra.yaml"])
    monkeypatch.setitem(
        settings.plugins,
        "embedded_demo",
        {
            "extra_config_path": str(yaml_path),
            "enabled": True,
            "api_key": "demo-api-key",
        },
    )

    response = client.get("/docs/plugin-config", params={"plugin": "embedded_demo"})

    assert response.status_code == 403
    assert response.json()["message"] == "Repository access denied: embedded_demo"


def test_get_plugin_config_documentation_rejects_settings_only_config_without_whitelist(
    client: TestClient, tmp_path, monkeypatch
):
    from framex.config import settings

    _set_oauth_session(client, monkeypatch)
    yaml_path = tmp_path / "proxy-extra.yaml"
    yaml_path.write_text("name: proxy\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings.docs, "embedded_config_file_whitelist", [])
    monkeypatch.setitem(
        settings.plugins,
        "embedded_demo_without_whitelist",
        {"extra_config_path": str(yaml_path), "enabled": True},
    )

    response = client.get("/docs/plugin-config", params={"plugin": "embedded_demo_without_whitelist"})

    assert response.status_code == 403
    assert response.json()["message"] == "Repository access denied: embedded_demo_without_whitelist"


def test_get_plugin_config_documentation(client: TestClient, monkeypatch):
    async def fake_is_private_repository(*_args) -> bool:
        return False

    monkeypatch.setattr("framex.driver.application.is_private_repository", fake_is_private_repository)
    _set_oauth_session(client, monkeypatch)
    response = client.get("/docs/plugin-config", params={"plugin": "proxy"})

    assert response.status_code == 200
    assert "Plugin Config (TOML)" in response.text
    assert "proxy_urls" in response.text


def test_get_plugin_config_documentation_requires_repository_access(client: TestClient, monkeypatch):
    _set_oauth_session(client, monkeypatch)

    async def fake_is_private_repository(*_args) -> bool:
        return True

    async def fake_can_access_repository(*_args) -> bool:
        return False

    monkeypatch.setattr("framex.driver.application.is_private_repository", fake_is_private_repository)
    monkeypatch.setattr("framex.driver.application.can_access_repository", fake_can_access_repository)

    response = client.get("/docs/plugin-config", params={"plugin": "proxy"})

    assert response.status_code == 403
    assert response.json()["message"] == "Repository access denied: proxy"


def test_get_plugin_config_documentation_checks_public_probe_before_token(client: TestClient, monkeypatch):
    called = {"can_access": 0, "is_private": 0}

    async def fake_can_access(*_args):
        called["can_access"] += 1
        return True

    async def fake_is_private(*_args):
        called["is_private"] += 1
        return False

    monkeypatch.setattr("framex.driver.application.can_access_repository", fake_can_access)
    monkeypatch.setattr("framex.driver.application.is_private_repository", fake_is_private)
    _set_oauth_session(client, monkeypatch)

    response = client.get("/docs/plugin-config", params={"plugin": "proxy"})

    assert response.status_code == 200
    assert called == {"can_access": 0, "is_private": 1}


def test_get_plugin_config_documentation_skips_repository_check_for_public_repo(client: TestClient, monkeypatch):
    async def fake_is_private_repository(*_args) -> bool:
        return False

    monkeypatch.setattr("framex.driver.application.is_private_repository", fake_is_private_repository)
    _set_oauth_session(client, monkeypatch)

    response = client.get("/docs/plugin-config", params={"plugin": "proxy"})

    assert response.status_code == 200
    assert "Plugin Config (TOML)" in response.text


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
    from framex.plugin.load import register_proxy_func

    asyncio.run(register_proxy_func(local_exchange_key_value))
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
