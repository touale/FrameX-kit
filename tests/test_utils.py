import html
import importlib
import json
from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel

from framex.config import AuthConfig, GitLabRepositoryAuthEndpointConfig, settings
from framex.repository import get_latest_repository_version, has_newer_release_version
from framex.utils import (
    StreamEnventType,
    build_plugin_config_html,
    build_plugin_description,
    cache_decode,
    cache_encode,
    format_uptime,
    make_stream_event,
    safe_error_message,
)


class StreamDataModel(BaseModel):
    content: str
    id: int


@pytest.mark.parametrize(
    ("event_type", "data", "result"),
    [
        ("event a", "data a", 'event: event a\ndata: {"content": "data a"}\n\n'),
        (
            StreamEnventType.MESSAGE_CHUNK,
            {"result": "chunk data"},
            'event: message_chunk\ndata: {"result": "chunk data"}\n\n',
        ),
        (
            StreamEnventType.DEBUG,
            StreamDataModel(content="data a", id=1),
            'event: debug\ndata: {"content": "data a", "id": 1}\n\n',
        ),
    ],
)
def test_make_stream_event(event_type: StreamEnventType | str, data: str | dict[str, Any] | BaseModel, result: str):
    res = make_stream_event(event_type, data)
    assert res == result


def test_is_url_protected():
    cfg = AuthConfig(
        rules={
            "/api/user": ["k1"],
            "/api/*": ["k2"],
        }
    )

    assert cfg._is_url_protected("/api/user")
    assert cfg._is_url_protected("/api/user/1")
    assert not cfg._is_url_protected("/admin")


def test_get_auth_keys():
    cfg = AuthConfig(
        rules={
            "/api/*": ["k1"],
            "/api/admin/*": ["k2"],
            "/api/admin/user": ["k3"],
        }
    )

    assert cfg.get_auth_keys("/public") is None
    assert cfg.get_auth_keys("/api/user") == ["k1"]
    assert cfg.get_auth_keys("/api/admin/test") == ["k2"]
    assert cfg.get_auth_keys("/api/admin/user") == ["k3"]


class SubModel(BaseModel):
    id: int
    name: str


class ExchangeModel(BaseModel):
    id: str
    name: int
    model: SubModel
    created_at: datetime


def test_basic_types():
    data = {"a": 1, "b": "string", "c": [1, 2, 3], "d": {"nested": True}}
    encoded = cache_encode(data)
    decoded = cache_decode(encoded)
    assert decoded == data
    assert isinstance(decoded["c"], list)


def test_datetime_and_enum():
    now = datetime(2025, 12, 23, 10, 0, 0)
    data = {"time": now}
    encoded = cache_encode(data)
    decoded = cache_decode(encoded)
    assert "2025-12-23T10:00:00" in str(decoded["time"])


def test_nested_pydantic_models():
    sub = SubModel(id=1, name="sub_name")
    main = ExchangeModel(id="main_id", name=100, model=sub, created_at=datetime.now())

    original_data = {"status": "success", "result_list": [main, main], "single_model": main}

    encoded = cache_encode(original_data)
    assert isinstance(encoded, str)

    decoded = cache_decode(encoded)

    res_model = decoded["single_model"]
    assert res_model.id == "main_id"
    assert res_model.name == 100

    assert isinstance(res_model.model, SubModel)
    assert res_model.model.id == 1
    assert res_model.model.name == "sub_name"

    assert decoded["result_list"][0].model.id == 1


def test_recovery_failure_fallback():
    fake_payload = {
        "__type__": "dynamic_obj",
        "__module__": "non.existent.module",
        "__class__": "MissingClass",
        "data": {"id": 999, "info": "test"},
    }
    encoded = json.dumps(fake_payload)
    decoded = cache_decode(encoded)

    assert decoded.id == 999
    assert decoded.info == "test"


def test_format_uptime():
    """Test format_uptime function"""
    # Test seconds only
    delta = timedelta(seconds=45)
    assert format_uptime(delta) == "45s"

    # Test minutes and seconds
    delta = timedelta(seconds=125)
    assert format_uptime(delta) == "2m 5s"

    # Test hours, minutes, and seconds
    delta = timedelta(seconds=3665)
    assert format_uptime(delta) == "1h 1m 5s"

    # Test days
    delta = timedelta(days=2, seconds=3661)
    assert format_uptime(delta) == "2d 1h 1m 1s"

    # Test zero seconds
    delta = timedelta(seconds=0)
    assert format_uptime(delta) == "0s"

    # Test only minutes (no seconds)
    delta = timedelta(minutes=5, seconds=0)
    assert format_uptime(delta) == "5m"


class CauseError(Exception):
    def __init__(self, cause: Exception):
        self.cause = cause
        super().__init__("outer")


def test_safe_error_message_with_cause():
    e = CauseError(RuntimeError("inner"))
    assert safe_error_message(e) == "inner"


def test_safe_error_message_with_args():
    e = RuntimeError("simple error")
    assert safe_error_message(e) == "simple error"


def test_safe_error_message_fallback():
    e = Exception()
    e.args = ()
    assert safe_error_message(e) == "Internal Server Error"


def test_build_plugin_description_shows_lazy_release_view():
    description = build_plugin_description(
        author="tester",
        version="v0.3.4",
        description="demo plugin",
        repo="https://github.com/example/repo",
        plugin_name="demo",
    )

    assert "/docs/plugin-release?plugin=demo" in description


def test_build_plugin_description_shows_config_view():
    class DemoConfig(BaseModel):
        enabled: bool = True
        name: str = "demo"

    description = build_plugin_description(
        author="tester",
        version="v0.3.4",
        description="demo plugin",
        repo="https://github.com/example/repo",
        plugin_name="demo",
    )

    assert "View Config" in description
    assert "/docs/plugin-config?plugin=demo" in description


def test_build_plugin_config_html_uses_toml_format():
    response = build_plugin_config_html(
        {
            "enabled": True,
            "name": "demo",
            "proxy_urls": ["https://example.com"],
            "nested": {"timeout": 30},
            "endpoints": [{"host": "gitlab.example.com", "token": "demo-token"}],
        }
    )

    body = html.unescape(response.body.decode())  # type: ignore
    assert "Plugin Config (TOML)" in body
    assert "enabled = true" in body
    assert 'name = "demo"' in body
    assert 'proxy_urls = ["https://example.com"]' in body
    assert "[nested]" in body
    assert "timeout = 30" in body
    assert "[[endpoints]]" in body
    assert 'host = "gitlab.example.com"' in body


def test_build_plugin_description_skips_lazy_release_view_without_plugin_name():
    description = build_plugin_description(
        author="tester",
        version="v0.3.4",
        description="demo plugin",
        repo="https://github.com/example/repo",
    )

    assert "/docs/plugin-release?plugin=" not in description
    assert "⬆️" not in description


def test_has_newer_release_version():
    assert has_newer_release_version("v0.3.4", "v0.3.5")
    assert not has_newer_release_version("v0.3.4", "v0.3.4")
    assert not has_newer_release_version("v0.3.4", "invalid")


def test_get_latest_repository_version_uses_github_auth_token(monkeypatch):
    get_latest_repository_version.cache_clear()
    monkeypatch.setattr(settings.repository.auth.github, "token", "gh-private-token")

    captured_headers: dict[str, str | None] = {}

    def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["authorization"] = (headers or {}).get("Authorization")
        return {"tag_name": "v1.2.3"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = get_latest_repository_version("https://github.com/example/private-repo")

    assert version == "v1.2.3"
    assert captured_headers["authorization"] == "Bearer gh-private-token"
    get_latest_repository_version.cache_clear()


def test_get_latest_repository_version_uses_gitlab_private_token(monkeypatch):
    get_latest_repository_version.cache_clear()
    monkeypatch.setattr(settings.repository.auth.gitlab, "token", "gitlab-private-token")

    captured_headers: dict[str, str | None] = {}

    def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["private_token"] = (headers or {}).get("PRIVATE-TOKEN")
        return {"tag_name": "v2.0.0"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = get_latest_repository_version("https://gitlab.com/example/private-repo")

    assert version == "v2.0.0"
    assert captured_headers["private_token"] == "gitlab-private-token"  # noqa
    get_latest_repository_version.cache_clear()


def test_get_latest_repository_version_uses_gitlab_endpoint_token(monkeypatch):
    get_latest_repository_version.cache_clear()
    monkeypatch.setattr(
        settings.repository.auth.gitlab,
        "endpoints",
        [
            GitLabRepositoryAuthEndpointConfig(
                host="gitlab.company.internal",
                path_prefix="/team-a",
                token="team-a-token",  # noqa
            )
        ],
    )

    captured_headers: dict[str, str | None] = {}

    def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["private_token"] = (headers or {}).get("PRIVATE-TOKEN")
        return {"tag_name": "v3.0.0"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = get_latest_repository_version("https://gitlab.company.internal/team-a/private-repo")

    assert version == "v3.0.0"
    assert captured_headers["private_token"] == "team-a-token"  # noqa
    get_latest_repository_version.cache_clear()


def test_repository_fetch_json_follows_redirects(monkeypatch):
    import framex.repository.providers.base as base_module

    base_module = importlib.reload(base_module)
    captured: dict[str, bool] = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, follow_redirects: bool = False):  # noqa
            captured["follow_redirects"] = follow_redirects
            response = type("Response", (), {})()
            response.status_code = 200
            response.json = lambda: {"tag_name": "v0.0.15"}
            return response

    monkeypatch.setattr(base_module.httpx, "Client", FakeClient)

    payload = base_module.RepositoryVersionProvider.fetch_json(
        "https://gitlab.company.internal/api/v4/projects/184/releases/permalink/latest"
    )

    assert payload == {"tag_name": "v0.0.15"}
    assert captured["follow_redirects"] is True
