from typing import Any

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, call_plugin_api, on_register, on_request


class EchoService:
    async def echo(self, message: str) -> str:
        result = await call_plugin_api("/api/v1/echo", message=message)
        assert isinstance(result, str)
        return result


__plugin_meta__ = PluginMetadata(
    name="ray_service_caller",
    version=VERSION,
    description="Ray integration test plugin for nested service plugin calls",
    author="tests",
    url="https://example.invalid",
    required_remote_apis=["/api/v1/echo"],
)


@on_register()
class RayServiceCallerPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        self.service = EchoService()
        super().__init__(**kwargs)

    @on_request("/service_echo", methods=["GET"])
    async def service_echo(self, message: str) -> str:
        return await self.service.echo(message)
