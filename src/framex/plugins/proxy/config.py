from pydantic import BaseModel


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str]
