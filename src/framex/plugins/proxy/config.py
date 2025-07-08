from pydantic import BaseModel


class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str]
    force_stream_apis: list[str]
