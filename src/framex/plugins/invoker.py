from typing import Any

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request

__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="原神会调用远程方法哟",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=["/api/v1/echo", "echo.EchoPlugin.confess", "/api/v1/echo_stream"],
)


@on_register()
class InvokerPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/evoke_echo", methods=["GET"])
    async def evoke(self, message: str) -> list[Any]:
        def extract_content(chunk: str) -> str:
            return chunk.split('"content": "')[-1].split('"')[0]

        echo = await self._call_remote_api("/api/v1/echo", message=message)
        stream = await self._call_remote_api("/api/v1/echo_stream", message=message)
        stream_text = "".join([extract_content(c) for c in stream if "message_chunk" in c])
        confess = await self._call_remote_api("echo.EchoPlugin.confess", message=message)

        return [echo, stream_text, confess]
