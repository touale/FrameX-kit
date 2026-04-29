from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.plugin.model import ApiType

__plugin_meta__ = PluginMetadata(
    name="websocket_demo",
    version=VERSION,
    description="WebSocket demo plugin",
    author="tests",
    url="https://example.invalid",
)


@on_register()
class WebSocketDemoPlugin(BasePlugin):
    @on_request("/ws/echo/{room}", call_type=ApiType.WEBSOCKET)
    async def echo(self, room: str, message: str) -> str:
        return f"{room}:{message}"
