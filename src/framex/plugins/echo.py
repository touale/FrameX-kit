import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.utils import StreamEnventType, make_stream_event

__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="原神会重复你说的话",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return message

    @on_request("/echo_stream", methods=["GET"], stream=True)
    async def echo_stream(self, message: str) -> AsyncGenerator[str, None]:
        for char in f"原神真好玩呀, {message}":
            yield make_stream_event(StreamEnventType.MESSAGE_CHUNK, char)
            await asyncio.sleep(0.1)
        yield make_stream_event(StreamEnventType.FINISH, char)
