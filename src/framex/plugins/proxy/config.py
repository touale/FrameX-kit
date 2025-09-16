from pydantic import BaseModel

from framex.plugin import get_plugin_config


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str] = []
    force_stream_apis: list[str] = []

    black_list: list[str] = []
    white_list: list[str] = []


settings = get_plugin_config("proxy", ProxyPluginConfig)
