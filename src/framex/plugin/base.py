from typing import Any, final

from framex.config import settings
from framex.log import setup_logger
from framex.plugin import call_plugin_api
from framex.plugin.model import PluginApi


class BasePlugin:
    """Base class for all plugins"""

    def __init__(self, **kwargs: Any) -> None:
        setup_logger()
        self.remote_apis: dict[str, PluginApi] = kwargs.get("remote_apis", {})
        if settings.server.use_ray:
            import asyncio

            asyncio.create_task(self.on_start())  # noqa: RUF006

    async def on_start(self) -> None:
        pass

    @final
    async def _call_remote_api(self, api_name: str, **kwargs: Any) -> Any:
        res = await call_plugin_api(api_name, self.remote_apis, **kwargs)
        return self._post_call_remote_api_hook(res)

    def _post_call_remote_api_hook(self, data: Any) -> Any:
        return data
