from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from framex.config import AuthConfig
from framex.plugin import get_plugin_config


class ProxyUrlRuleConfig(BaseModel):
    enable: list[str] = Field(default_factory=list)
    disable: list[str] = Field(default_factory=list)


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str] | dict[str, ProxyUrlRuleConfig] = Field(default_factory=list)
    force_stream_apis: list[str] = Field(default_factory=list)
    timeout: int = 600
    ingress_config: dict[str, Any] = Field(default_factory=lambda: {"max_ongoing_requests": 60})

    white_list: list[str] = Field(default=["/*"])

    auth: AuthConfig = Field(default_factory=AuthConfig)

    proxy_functions: dict[str, list[str]] = Field(default_factory=dict)

    def is_white_url(self, base_url: str, path: str) -> bool:
        """
        Return True if the path is allowed by white rules.
        Base_url specific rules take precedence.
        """

        if isinstance(self.proxy_urls, dict):
            config = self.proxy_urls.get(base_url)
            if config is not None:
                if self._match_rules(config.disable, path):
                    return False

                if self._match_rules(config.enable, path):
                    return True

        # fallback global rule
        return self._match_rules(self.white_list, path)

    @staticmethod
    def _match_rules(white_list: list[str], path: str) -> bool:
        for rule in white_list:
            if rule == "/*":
                return True
            if rule == path:
                return True
            if rule.endswith("/*") and path.startswith(rule[:-1]):
                return True
        return False

    @property
    def proxy_url_list(self) -> list[str]:
        if isinstance(self.proxy_urls, list):
            return self.proxy_urls
        if isinstance(self.proxy_urls, dict):
            return list(self.proxy_urls.keys())
        raise TypeError("Invalid proxy_urls type")  # pragma: no cover

    @model_validator(mode="after")
    def validate_proxy_functions(self) -> Self:
        for url in self.proxy_functions:
            if url not in self.proxy_url_list:  # pragma: no cover
                raise ValueError(f"proxy_functions url '{url}' is not covered by any proxy_urls rule")
        return self


settings: ProxyPluginConfig = get_plugin_config("proxy", ProxyPluginConfig)
