from typing import Any

from pydantic import BaseModel

from framex.config import AuthConfig
from framex.plugin import get_plugin_config


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str] = []
    force_stream_apis: list[str] = []
    timeout: int = 600
    ingress_config: dict[str, Any] = {"max_ongoing_requests": 60}

    white_list: list[str] = []

    auth: AuthConfig = AuthConfig()


settings = get_plugin_config("proxy", ProxyPluginConfig)
