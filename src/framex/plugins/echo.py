import asyncio
from collections.abc import AsyncGenerator, Callable
from typing import Any

from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.plugin.model import ApiType
from framex.utils import StreamEnventType, make_stream_event

__plugin_meta__ = PluginMetadata(
    name="echo",
    version=VERSION,
    description="原神会重复你说的话",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


class EchoModel(BaseModel):
    id: int
    name: str = "原神"


@on_register()
class EchoPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @on_request("/echo", methods=["GET"])
    async def echo(self, message: str) -> str:
        return message

    @on_request("/echo_model", methods=["POST"])
    async def echo_model(self, message: str, model: EchoModel) -> str:
        return f"{message},{model.model_dump()}"

    @on_request("/api/v1/echo_stream", methods=["GET"], stream=True)
    async def echo_stream(self, message: str) -> AsyncGenerator[str, None]:
        for char in f"原神真好玩呀, {message}":
            yield make_stream_event(StreamEnventType.MESSAGE_CHUNK, char)
            await asyncio.sleep(0.1)
        yield make_stream_event(StreamEnventType.FINISH)

    @on_request(call_type=ApiType.FUNC)
    async def confess(self, message: str, call_back: Callable) -> str:
        call_back_result = call_back(message)
        return f"我是原神哟! 收到message={message},call_back_result={call_back_result}"
