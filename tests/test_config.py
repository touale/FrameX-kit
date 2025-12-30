from framex.config import OauthConfig


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
