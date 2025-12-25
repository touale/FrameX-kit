from framex.config import AuthConfig


def test_config():
    from framex.plugin import get_plugin_config
    from framex.plugins.proxy.config import ProxyPluginConfig

    cfg = get_plugin_config("proxy", ProxyPluginConfig)
    assert isinstance(cfg, ProxyPluginConfig)
    assert cfg.proxy_urls is not None


def test_auth_config():
    AuthConfig(
        general_auth_keys=["abcdefg"],
        auth_urls=[
            "/api/v1/a/*",
            "/api/b/call",
            "/api/v1/c/*",
        ],
        special_auth_keys={"/api/v1/a/call": ["0123456789"], "/api/v1/c/*": ["0123456789a", "0123456789b"]},
    )

    AuthConfig(
        general_auth_keys=["abcdefg"],
        auth_urls=[
            "/api/v1/a/*",
        ],
        special_auth_keys={"/api/v1/a/call": ["0123456789"]},
    )
