import re

import pytest
from pydantic import BaseModel, ValidationError

from framex.config import CacheConfig, OauthConfig, RepositoryConfig, Settings

JWT_SECRET = "test-secret-with-enough-bytes-for-hs256"  # noqa: S105


def test_config():
    from framex.plugin import get_plugin_config
    from framex.plugins.proxy.config import ProxyPluginConfig

    cfg = get_plugin_config("proxy", ProxyPluginConfig)
    assert isinstance(cfg, ProxyPluginConfig)
    assert cfg.proxy_urls is not None


def test_get_plugin_config_rejects_unknown_fields(monkeypatch):
    from framex.config import settings
    from framex.plugin import get_plugin_config

    class PluginConfig(BaseModel):
        enabled: bool = False
        timeout: int = 30

    monkeypatch.setitem(
        settings.plugins,
        "invalid_config",
        {"unknown_z": True, "enabled": True, "unknown_a": False},
    )
    get_plugin_config.cache_clear()

    try:
        with pytest.raises(ValueError, match="unknown config fields") as exc_info:
            get_plugin_config("invalid_config", PluginConfig)

        assert str(exc_info.value) == (
            "Plugin(invalid_config) has unknown config fields: unknown_a, unknown_z. "
            "Only these fields are allowed: enabled, timeout"
        )
    finally:
        get_plugin_config.cache_clear()


@pytest.mark.parametrize(
    ("toml_content", "unknown_field"),
    [
        ("unknown_option = true\n", "unknown_option"),
        ("[server]\nunknown_option = true\n", "server.unknown_option"),
    ],
)
def test_settings_rejects_unknown_toml_fields(tmp_path, toml_content, unknown_field):
    from pydantic_settings import TomlConfigSettingsSource

    from framex.config import Settings

    toml_path = tmp_path / "config.toml"
    toml_path.write_text(toml_content, encoding="utf-8")
    toml_source = TomlConfigSettingsSource(Settings, toml_file=toml_path)

    with pytest.raises(ValidationError, match=re.escape(unknown_field)):
        Settings(_build_sources=((toml_source,), {}))


def test_oauth_config_callback_url_property():
    cfg = OauthConfig(
        app_url="https://example.com",
        redirect_uri="/auth/callback",
        jwt_secret=JWT_SECRET,
    )
    assert cfg.call_back_url == "https://example.com/auth/callback"


def test_cache_config_defaults():
    cfg = CacheConfig()

    assert cfg.enabled is False
    assert cfg.mode == "memory"
    assert cfg.ttl == 60
    assert cfg.max_size == 1000
    assert cfg.file_dir == ".framex/cache"


def test_settings_base_ingress_config_defaults_include_health_checks():
    default_config = Settings.model_fields["base_ingress_config"].get_default(call_default_factory=True)

    assert default_config == {
        "max_ongoing_requests": 10,
        "health_check_period_s": 15,
        "health_check_timeout_s": 60,
    }


def test_cache_config_validates_mode_ttl_and_max_size():
    with pytest.raises(ValidationError):
        CacheConfig(mode="redis")  # type: ignore[arg-type]
    assert CacheConfig(ttl=-1).ttl == -1
    with pytest.raises(ValidationError):
        CacheConfig(ttl=0)
    with pytest.raises(ValidationError):
        CacheConfig(max_size=0)


def test_oauth_config_generates_default_urls_from_base_url():
    cfg = OauthConfig(
        base_url="https://gitlab.example.com",
        jwt_secret=JWT_SECRET,
    )

    assert cfg.authorization_url == "https://gitlab.example.com/oauth/authorize"
    assert cfg.token_url == "https://gitlab.example.com/oauth/token"  # noqa: S105
    assert cfg.user_info_url == "https://gitlab.example.com/api/v4/user"


def test_oauth_config_requires_fixed_jwt_secret():
    with pytest.raises(ValidationError, match="jwt_secret"):
        OauthConfig()  # type: ignore[call-arg]

    with pytest.raises(ValidationError, match="at least 32 UTF-8 bytes"):
        OauthConfig(jwt_secret="too-short")  # noqa: S106

    utf8_secret = "密钥" * 6
    assert len(utf8_secret) < 32
    assert len(utf8_secret.encode("utf-8")) >= 32
    assert OauthConfig(jwt_secret=utf8_secret).jwt_secret == utf8_secret


def test_oauth_config_cookie_secure_defaults_from_app_url():
    assert OauthConfig(app_url="https://framex.example.test", jwt_secret=JWT_SECRET).use_secure_cookie is True
    assert OauthConfig(app_url="http://127.0.0.1:8080", jwt_secret=JWT_SECRET).use_secure_cookie is False


def test_oauth_config_does_not_override_custom_urls():
    cfg = OauthConfig(
        base_url="https://gitlab.example.com",
        authorization_url="https://custom.auth",
        token_url="https://custom.token",  # noqa: S106
        user_info_url="https://custom.user",
        jwt_secret=JWT_SECRET,
    )

    assert cfg.authorization_url == "https://custom.auth"
    assert cfg.token_url == "https://custom.token"  # noqa: S105
    assert cfg.user_info_url == "https://custom.user"


def test_proxy_config():
    from framex.plugins.proxy.config import ProxyPluginConfig, ProxyUrlRuleConfig

    proxy_config = ProxyPluginConfig(
        proxy_urls={
            "http://localhost:10000": ProxyUrlRuleConfig(enable=["/*"], disable=["/health"]),
            "http://localhost:10001": ProxyUrlRuleConfig(enable=["/*"]),
        },
    )
    assert not proxy_config.is_white_url("http://localhost:10000", "/health")
    assert proxy_config.is_white_url("http://localhost:10000", "/echo")
    assert proxy_config.is_white_url("http://localhost:10001", "/health")


def test_repository_auth_config_default_headers():
    cfg = RepositoryConfig()

    assert cfg.auth.github.build_headers() == {}
    assert cfg.auth.gitlab.build_headers() == {}


def test_repository_auth_config_builds_provider_headers():
    cfg = RepositoryConfig(
        auth={
            "github": {"token": "gh-secret"},
            "gitlab": {"token": "gl-secret"},
        }
    )

    assert cfg.auth.github.build_headers() == {"Authorization": "Bearer gh-secret"}
    assert cfg.auth.gitlab.build_headers() == {"PRIVATE-TOKEN": "gl-secret"}


def test_gitlab_repository_auth_config_uses_matching_endpoint_headers():
    cfg = RepositoryConfig(
        auth={
            "gitlab": {
                "endpoints": [
                    {"host": "gitlab.internal.test", "token": "team-a-token", "path_prefix": "/team-a"},
                    {"host": "gitlab.internal.test", "token": "team-b-token", "path_prefix": "/team-b"},
                ]
            }
        }
    )

    assert cfg.auth.gitlab.build_headers_for_url("gitlab.internal.test", "/team-a/repo") == {
        "PRIVATE-TOKEN": "team-a-token"
    }
    assert cfg.auth.gitlab.build_headers_for_url("gitlab.internal.test", "/team-b/repo") == {
        "PRIVATE-TOKEN": "team-b-token"
    }


def test_gitlab_repository_auth_config_prefers_longest_path_prefix():
    cfg = RepositoryConfig(
        auth={
            "gitlab": {
                "endpoints": [
                    {"host": "gitlab.internal.test", "token": "group-token", "path_prefix": "/team"},
                    {"host": "gitlab.internal.test", "token": "project-token", "path_prefix": "/team/project"},
                ]
            }
        }
    )

    assert cfg.auth.gitlab.build_headers_for_url("gitlab.internal.test", "/team/project/repo") == {
        "PRIVATE-TOKEN": "project-token"
    }
