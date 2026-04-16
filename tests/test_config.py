from framex.config import OauthConfig, RepositoryConfig


def test_config():
    from framex.plugin import get_plugin_config
    from framex.plugins.proxy.config import ProxyPluginConfig

    cfg = get_plugin_config("proxy", ProxyPluginConfig)
    assert isinstance(cfg, ProxyPluginConfig)
    assert cfg.proxy_urls is not None


def test_oauth_config_callback_url_property():
    cfg = OauthConfig(
        app_url="https://example.com",
        redirect_uri="/auth/callback",
    )
    assert cfg.call_back_url == "https://example.com/auth/callback"


def test_oauth_config_generates_default_urls_from_base_url():
    cfg = OauthConfig(
        base_url="https://gitlab.example.com",
    )

    assert cfg.authorization_url == "https://gitlab.example.com/oauth/authorize"
    assert cfg.token_url == "https://gitlab.example.com/oauth/token"  # noqa: S105
    assert cfg.user_info_url == "https://gitlab.example.com/api/v4/user"


def test_oauth_config_generates_jwt_secret_when_missing():
    cfg = OauthConfig()
    assert cfg.jwt_secret
    assert isinstance(cfg.jwt_secret, str)
    assert len(cfg.jwt_secret) >= 32


def test_oauth_config_does_not_override_custom_urls():
    cfg = OauthConfig(
        base_url="https://gitlab.example.com",
        authorization_url="https://custom.auth",
        token_url="https://custom.token",  # noqa: S106
        user_info_url="https://custom.user",
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
                    {"host": "gitlab.company.internal", "token": "team-a-token", "path_prefix": "/team-a"},
                    {"host": "gitlab.company.internal", "token": "team-b-token", "path_prefix": "/team-b"},
                ]
            }
        }
    )

    assert cfg.auth.gitlab.build_headers_for_url("gitlab.company.internal", "/team-a/repo") == {
        "PRIVATE-TOKEN": "team-a-token"
    }
    assert cfg.auth.gitlab.build_headers_for_url("gitlab.company.internal", "/team-b/repo") == {
        "PRIVATE-TOKEN": "team-b-token"
    }


def test_gitlab_repository_auth_config_prefers_longest_path_prefix():
    cfg = RepositoryConfig(
        auth={
            "gitlab": {
                "endpoints": [
                    {"host": "gitlab.company.internal", "token": "group-token", "path_prefix": "/team"},
                    {"host": "gitlab.company.internal", "token": "project-token", "path_prefix": "/team/project"},
                ]
            }
        }
    )

    assert cfg.auth.gitlab.build_headers_for_url("gitlab.company.internal", "/team/project/repo") == {
        "PRIVATE-TOKEN": "project-token"
    }
