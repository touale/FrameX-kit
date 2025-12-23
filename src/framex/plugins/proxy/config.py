from typing import Any, Self

from pydantic import BaseModel, model_validator

from framex.config import AuthConfig
from framex.plugin import get_plugin_config


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str] = []
    force_stream_apis: list[str] = []
    timeout: int = 600
    ingress_config: dict[str, Any] = {"max_ongoing_requests": 60}

    white_list: list[str] = []

    auth: AuthConfig = AuthConfig()

    proxy_functions: dict[str, list[str]] = {}

    def is_white_url(self, url: str) -> bool:
        """Check if a URL is protected by any auth_urls rule."""
        if self.white_list == []:  # pragma: no cover
            return True
        for rule in self.white_list:
            if rule == url:
                return True
            if rule.endswith("/*") and url.startswith(rule[:-1]):
                return True
        return False

    @model_validator(mode="after")
    def validate_proxy_functions(self) -> Self:
        for url in self.proxy_functions:
            if url not in self.proxy_urls:  # pragma: no cover
                raise ValueError(f"proxy_functions url '{url}' is not covered by any proxy_urls rule")
        return self


settings = get_plugin_config("proxy", ProxyPluginConfig)
