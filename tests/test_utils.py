import html
import importlib
import json
from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from framex.config import (
    AuthConfig,
    DocsActionButtonConfig,
    DocsActionButtonInputConfig,
    GitLabRepositoryAuthEndpointConfig,
    settings,
)
from framex.repository import can_access_repository, get_latest_repository_version, has_newer_release_version
from framex.utils import (
    StreamEnventType,
    build_docs_action_button_views,
    build_plugin_config_html,
    build_plugin_description,
    build_swagger_ui_html,
    cache_decode,
    cache_encode,
    collect_embedded_config_files,
    format_uptime,
    make_stream_event,
    mask_sensitive_config_data,
    mask_sensitive_config_text,
    mask_sensitive_embedded_config_content,
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


def test_docs_action_button_auth_config_defaults_to_no_auth():
    config = DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo")

    assert config.auth.type == "none"
    assert config.timeout == 30.0
    assert config.requires_confirmation is False
    assert config.confirmation_message == ""


def test_docs_action_button_timeout_accepts_positive_override():
    config = DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo", timeout=12.5)

    assert config.timeout == 12.5


def test_docs_action_button_timeout_must_be_positive():
    with pytest.raises(ValidationError):
        DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo", timeout=0)


@pytest.mark.parametrize(
    "auth_config",
    [
        {"type": "none"},
        {"type": "oauth", "allowed_usernames": ["*"]},
        {"type": "oauth", "allowed_usernames": ["alice"]},
        {"type": "password", "password": "secret"},
    ],
)
def test_docs_action_button_auth_config_accepts_supported_modes(auth_config: dict[str, Any]):
    config = DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo", auth=auth_config)

    assert config.auth.type == auth_config["type"]


def test_docs_action_button_password_auth_requires_password():
    with pytest.raises(ValidationError):
        DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo", auth={"type": "password"})


def test_docs_action_button_rejects_unknown_auth_type():
    with pytest.raises(ValidationError):
        DocsActionButtonConfig(title="Echo", url="http://localhost:11000/api/v1/echo", auth={"type": "api_key"})


def test_build_docs_action_button_views_excludes_sensitive_request_config():
    views = build_docs_action_button_views(
        [
            DocsActionButtonConfig(
                title="Trigger CI",
                variant="success",
                requires_confirmation=True,
                confirmation_message="Confirm trigger?",
                url="https://example.test/trigger",
                headers={"Authorization": "Bearer secret-token"},
                body_type="form",
                body={"token": "secret-token"},
                auth={"type": "password", "password": "action-password"},
                inputs=[
                    DocsActionButtonInputConfig(
                        name="variables[PACKAGE_VERSION]",
                        label="Package Version",
                        placeholder="0.0.8",
                        default="0.0.8",
                        required=True,
                    )
                ],
            )
        ]
    )

    assert views == [
        {
            "index": 0,
            "title": "Trigger CI",
            "variant": "success",
            "requires_confirmation": True,
            "confirmation_message": "Confirm trigger?",
            "auth_type": "password",
            "inputs": [
                {
                    "name": "variables[PACKAGE_VERSION]",
                    "label": "Package Version",
                    "placeholder": "0.0.8",
                    "default": "0.0.8",
                    "required": True,
                    "target": "body",
                }
            ],
        }
    ]
    assert "url" not in views[0]
    assert "headers" not in views[0]
    assert "body" not in views[0]
    assert "auth" not in views[0]
    assert "password" not in views[0]


def test_build_swagger_ui_html_renders_action_button_metadata_without_secrets():
    html_response = build_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title="FrameX Docs",
        action_buttons=[
            {
                "index": 0,
                "title": "Trigger CI",
                "variant": "success",
                "requires_confirmation": True,
                "confirmation_message": "Confirm trigger?",
                "auth_type": "password",
                "inputs": [
                    {
                        "name": "variables[PACKAGE_VERSION]",
                        "label": "Package Version",
                        "placeholder": "0.0.8",
                        "default": "0.0.8",
                        "required": True,
                        "target": "body",
                    }
                ],
            }
        ],
    )
    html_text = html_response.body.decode()  # type: ignore

    assert "Trigger CI" in html_text
    assert "docs-action-button-success" in html_text
    assert "variables[PACKAGE_VERSION]" in html_text
    assert "Confirm trigger?" in html_text
    assert '"auth_type": "password"' in html_text
    assert "/docs/action-buttons/" in html_text
    assert "secret-token" not in html_text
    assert "action-password" not in html_text
    assert "allowed_usernames" not in html_text
    assert "https://example.test/trigger" not in html_text


def test_collect_embedded_config_files_reads_yaml_and_toml(tmp_path):
    yaml_path = tmp_path / "demo.yaml"
    yaml_path.write_text("name: demo\n", encoding="utf-8")
    toml_path = tmp_path / "demo.toml"
    toml_path.write_text('name = "demo"\n', encoding="utf-8")

    embedded_files = collect_embedded_config_files(
        {
            "yaml_path": str(yaml_path),
            "nested": {"toml_path": str(toml_path)},
            "ignored": str(tmp_path / "demo.json"),
        },
        workspace_root=tmp_path,
        whitelist=["*.yaml", "*.toml"],
    )

    assert embedded_files == [
        (str(yaml_path.resolve()), "name: demo\n"),
        (str(toml_path.resolve()), 'name = "demo"\n'),
    ]


def test_collect_embedded_config_files_requires_whitelist(tmp_path):
    yaml_path = tmp_path / "demo.yaml"
    yaml_path.write_text("name: demo\n", encoding="utf-8")

    embedded_files = collect_embedded_config_files(
        {"yaml_path": str(yaml_path)},
        workspace_root=tmp_path,
        whitelist=[],
    )

    assert embedded_files == []


def test_collect_embedded_config_files_blocks_outside_workspace(tmp_path):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_yaml_path = tmp_path / "outside.yaml"
    outside_yaml_path.write_text("name: outside\n", encoding="utf-8")

    embedded_files = collect_embedded_config_files(
        {"yaml_path": str(outside_yaml_path)},
        workspace_root=workspace_root,
        whitelist=["*.yaml"],
    )

    assert embedded_files == []


def test_mask_sensitive_config_data_masks_nested_values():
    masked = mask_sensitive_config_data(
        {
            "token": "abcdef123456",
            "nested": {"client_secret": "secret-value"},
            "headers": [{"authorization": "Bearer demo-token"}],
            "safe": "visible",
        }
    )

    assert masked["token"] != "abcdef123456"  # noqa
    assert masked["nested"]["client_secret"] != "secret-value"  # noqa
    assert masked["headers"][0]["authorization"] != "Bearer demo-token"
    assert masked["safe"] == "visible"


def test_mask_sensitive_config_data_masks_auth_rules_values():
    masked = mask_sensitive_config_data(
        {
            "auth": {
                "rules": {
                    "/api/v1/*": ["Basic YWRtaW46Z3podQ=="],
                    "/proxy/mock/auth/*": ["i_am_proxy_general_auth_keys"],
                }
            }
        }
    )

    assert masked["auth"]["rules"]["/api/v1/*"][0] != "Basic YWRtaW46Z3podQ=="
    assert masked["auth"]["rules"]["/proxy/mock/auth/*"][0] != "i_am_proxy_general_auth_keys"


def test_mask_sensitive_config_text_masks_yaml_and_toml_lines():
    content = "\n".join(  # noqa
        [
            'token = "abcdef123456"',
            "client_secret: secret-value",
            'safe = "visible"',
        ]
    )

    masked = mask_sensitive_config_text(content)

    assert 'token = "abcdef123456"' not in masked
    assert "client_secret: secret-value" not in masked
    assert 'safe = "visible"' in masked


def test_mask_sensitive_embedded_config_content_parses_yaml_and_toml():
    yaml_masked = mask_sensitive_embedded_config_content(
        "demo.yaml",
        "token: abcdef123456\nnested:\n  client_secret: secret-value\nsafe: visible\n",
    )
    toml_masked = mask_sensitive_embedded_config_content(
        "demo.toml",
        'token = "abcdef123456"\n[nested]\nclient_secret = "secret-value"\nsafe = "visible"\n',
    )

    assert "abcdef123456" not in yaml_masked
    assert "secret-value" not in yaml_masked
    assert "safe: visible" in yaml_masked
    assert "abcdef123456" not in toml_masked
    assert "secret-value" not in toml_masked
    assert 'safe = "visible"' in toml_masked


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
    assert 'token = "demo-token"' not in body


def test_build_plugin_config_html_hides_restricted_embedded_paths(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    allowed_path = workspace_root / "configs" / "allowed.yaml"
    allowed_path.parent.mkdir()
    allowed_path.write_text("name: demo\n", encoding="utf-8")

    outside_path = tmp_path / "secret.yaml"
    outside_path.write_text("token: secret\n", encoding="utf-8")

    monkeypatch.chdir(workspace_root)
    monkeypatch.setattr(settings.docs, "embedded_config_file_whitelist", ["configs/*.yaml"])

    response = build_plugin_config_html(
        {
            "allowed_config": str(allowed_path),
            "blocked_config": str(outside_path),
        }
    )

    body = html.unescape(response.body.decode())  # type: ignore
    assert 'allowed_config = "configs/allowed.yaml"' in body
    assert 'blocked_config = "[restricted config path]"' in body
    assert str(outside_path) not in body


def test_has_newer_release_version():
    assert has_newer_release_version("v0.3.4", "v0.3.5")
    assert not has_newer_release_version("v0.3.4", "v0.3.4")
    assert not has_newer_release_version("v0.3.4", "invalid")


async def test_get_latest_repository_version_uses_github_auth_token(monkeypatch):
    monkeypatch.setattr(settings.repository.auth.github, "token", "gh-private-token")

    captured_headers: dict[str, str | None] = {}

    async def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["authorization"] = (headers or {}).get("Authorization")
        return {"tag_name": "v1.2.3"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = await get_latest_repository_version("https://github.com/example/private-repo")

    assert version == "v1.2.3"
    assert captured_headers["authorization"] == "Bearer gh-private-token"


async def test_get_latest_repository_version_uses_gitlab_private_token(monkeypatch):
    monkeypatch.setattr(settings.repository.auth.gitlab, "token", "gitlab-private-token")
    monkeypatch.setattr(
        settings.repository.auth.gitlab,
        "endpoints",
        [GitLabRepositoryAuthEndpointConfig(host="gitlab.example.test", token="gitlab-private-token")],  # noqa
    )

    captured_headers: dict[str, str | None] = {}

    async def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["private_token"] = (headers or {}).get("PRIVATE-TOKEN")
        return {"tag_name": "v2.0.0"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = await get_latest_repository_version("https://gitlab.com/example/private-repo")

    assert version == "v2.0.0"
    assert captured_headers["private_token"] == "gitlab-private-token"  # noqa


async def test_get_latest_repository_version_uses_gitlab_endpoint_token(monkeypatch):
    monkeypatch.setattr(
        settings.repository.auth.gitlab,
        "endpoints",
        [
            GitLabRepositoryAuthEndpointConfig(
                host="gitlab.internal.test",
                path_prefix="/team-a",
                token="team-a-token",  # noqa
            )
        ],
    )

    captured_headers: dict[str, str | None] = {}

    async def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_headers["private_token"] = (headers or {}).get("PRIVATE-TOKEN")
        return {"tag_name": "v3.0.0"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = await get_latest_repository_version("https://gitlab.internal.test/team-a/private-repo")

    assert version == "v3.0.0"
    assert captured_headers["private_token"] == "team-a-token"  # noqa


async def test_get_latest_repository_version_resolves_gitlab_project_from_subdirectory_url(monkeypatch):
    monkeypatch.setattr(settings.repository.auth.gitlab, "token", "gitlab-private-token")
    monkeypatch.setattr(
        settings.repository.auth.gitlab,
        "endpoints",
        [GitLabRepositoryAuthEndpointConfig(host="gitlab.example.test", token="gitlab-private-token")],  # noqa
    )

    captured_urls: list[str] = []

    async def fake_can_fetch(url: str, headers: dict[str, str] | None = None):
        captured_urls.append(url)
        return url.endswith("/api/v4/projects/example-group%2Fexample-repo")

    async def fake_fetch_json(url: str, headers: dict[str, str] | None = None):
        captured_urls.append(url)
        return {"tag_name": "v4.0.0"}

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.can_fetch",
        staticmethod(fake_can_fetch),
    )
    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.fetch_json",
        staticmethod(fake_fetch_json),
    )

    version = await get_latest_repository_version(
        "https://gitlab.example.test/example-group/example-repo/plugins/example-plugin"
    )

    assert version == "v4.0.0"
    assert any(url.endswith("/api/v4/projects/example-group%2Fexample-repo") for url in captured_urls)
    assert any(
        url.endswith("/api/v4/projects/example-group%2Fexample-repo/releases/permalink/latest")
        for url in captured_urls
    )


async def test_can_access_repository_resolves_gitlab_project_from_subdirectory_url(monkeypatch):
    monkeypatch.setattr(
        settings.repository.auth.gitlab,
        "endpoints",
        [GitLabRepositoryAuthEndpointConfig(host="gitlab.example.test", token="gitlab-private-token")],  # noqa
    )
    captured: dict[str, object] = {"urls": []}

    async def fake_can_fetch(
        url: str,
        headers: dict[str, str] | None = None,
        *,
        follow_redirects: bool = True,
    ):
        captured["urls"].append(url)  # type: ignore
        captured["authorization"] = (headers or {}).get("Authorization")  # type: ignore
        return url.endswith("/api/v4/projects/example-group%2Fexample-repo")

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.can_fetch",
        staticmethod(fake_can_fetch),
    )

    has_access = await can_access_repository(
        "https://gitlab.example.test/example-group/example-repo/plugins/example-plugin",
        "gitlab",
        "oauth-token",
    )

    assert has_access is True
    assert any(
        url.endswith("/api/v4/projects/example-group%2Fexample-repo")
        for url in captured["urls"]  # type: ignore
    )
    assert captured["authorization"] == "Bearer oauth-token"


async def test_gitlab_public_repository_probe_disables_redirects(monkeypatch):
    from urllib.parse import urlparse

    from framex.repository.providers.gitlab import GitLabRepositoryVersionProvider

    captured: dict[str, object] = {}

    async def fake_can_fetch(
        url: str,
        headers: dict[str, str] | None = None,
        *,
        follow_redirects: bool = True,
    ) -> bool:
        captured["url"] = url
        captured["follow_redirects"] = follow_redirects
        return False

    monkeypatch.setattr(
        "framex.repository.providers.base.RepositoryVersionProvider.can_fetch",
        staticmethod(fake_can_fetch),
    )

    provider = GitLabRepositoryVersionProvider()
    await provider.is_public_repository(
        urlparse("https://gitlab.example.test/example-group/example-repo/plugins/example-plugin")
    )

    assert captured["url"] == ("https://gitlab.example.test/example-group/example-repo/plugins/example-plugin")
    assert captured["follow_redirects"] is False


async def test_repository_fetch_json_follows_redirects(monkeypatch):
    import framex.repository.providers.base as base_module

    base_module = importlib.reload(base_module)
    captured: dict[str, bool] = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, follow_redirects: bool = False):  # noqa
            captured["follow_redirects"] = follow_redirects
            response = type("Response", (), {})()
            response.status_code = 200
            response.json = lambda: {"tag_name": "v0.0.15"}
            return response

    monkeypatch.setattr(base_module.httpx, "AsyncClient", FakeClient)

    payload = await base_module.RepositoryVersionProvider.fetch_json(
        "https://gitlab.internal.test/api/v4/projects/184/releases/permalink/latest"
    )

    assert payload == {"tag_name": "v0.0.15"}
    assert captured["follow_redirects"] is True
