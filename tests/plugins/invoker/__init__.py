import time
from typing import Any

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request, remote

__plugin_meta__ = PluginMetadata(
    name="invoker",
    version=VERSION,
    description="原神会调用远程方法哟",
    author="原神",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[
        "/api/v1/echo",
        "echo.EchoPlugin.confess",
        "/api/v1/echo_stream",
        "/api/v1/echo_model",
        "/api/v1/alias/info",
        "alias_model.AliasDemoPlugin.get_user_info",
    ],
)


@on_register()
class InvokerPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @staticmethod
    @remote()
    def remote_sleep() -> str:
        time.sleep(0.1)
        return "remote_sleep"

    @staticmethod
    @remote()
    def remote_func_with_params(a: str) -> str:
        return f"remote_func_with_params: {a}"

    @staticmethod
    @remote()
    async def remote_func_async() -> str:
        return "remote_func_async"

    @staticmethod
    @remote()
    async def remote_func_async_with_params(a: int, b: str) -> str:
        return f"remote_func_async_with_params: {a},{b}"

    @on_request("/evoke_echo", methods=["GET"])
    async def evoke(self, message: str) -> list[Any]:
        def extract_content(chunk: str) -> str:
            return chunk.split('"content": "')[-1].split('"')[0]

        call_back = lambda x: "hello" + x  # noqa

        # Call the remote sleep function
        remote_res = (
            await self.remote_sleep.remote()
            + await self.remote_func_with_params.remote("123")
            + await self.remote_func_async.remote()
            + await self.remote_func_async_with_params.remote(100, "abc")
        )

        echo = await self._call_remote_api("/api/v1/echo", message=message)
        stream = await self._call_remote_api("/api/v1/echo_stream", message=message)
        stream_text = "".join([extract_content(c) for c in stream if "message_chunk" in c])
        confess = await self._call_remote_api("echo.EchoPlugin.confess", message=message, call_back=call_back)
        echo_model = await self._call_remote_api(
            "/api/v1/echo_model", message=message, model={"id": 1, "name": "原神"}
        )
        alias_user_info = await self._call_remote_api("/api/v1/alias/info")
        alias_func_user_info = await self._call_remote_api("alias_model.AliasDemoPlugin.get_user_info")

        return [
            echo,
            stream_text,
            confess,
            echo_model,
            remote_res,
            alias_user_info,
            alias_func_user_info,
        ]
