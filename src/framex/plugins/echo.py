from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def __call__(self, message: str):
        return message
