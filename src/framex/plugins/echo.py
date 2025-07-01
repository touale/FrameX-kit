from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginApi, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="重复你说的话",
    author="yuanshen",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, remote_apis: dict[str, PluginApi]):
        super().__init__(remote_apis)

    @on_request("/echo", methods=["GET"])
    async def __call__(self, message: str):
        return message
