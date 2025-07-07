import asyncio
from typing import final

from pydantic import BaseModel

from framex.plugin import call_remote_api
from framex.plugin.model import PluginApi


class BasePlugin:
    """Base class for all plugins"""

    def __init__(self, **kwargs):
        self.remote_apis: dict[str, PluginApi] = kwargs.get("remote_apis", {})
        asyncio.create_task(self.on_start())  # noqa

    async def on_start(self):
        pass

    @final
    async def _call_remote_api(self, api_name: str, **kwargs):
        if not (api := self.remote_apis.get(api_name)):
            raise RuntimeError(
                f"API {api_name} is not required by this plugin, current plugins: {self.remote_apis.keys()}"
            )

        param_type_map = dict(api.params)
        for key, val in kwargs.items():
            if (
                isinstance(val, dict)
                and (expected_type := param_type_map.get(key))
                and isinstance(expected_type, type)
                and issubclass(expected_type, BaseModel)
            ):
                try:
                    kwargs[key] = expected_type(**val)
                except Exception as e:
                    raise RuntimeError(f"Failed to convert '{key}' to {expected_type}") from e

        return await call_remote_api(api, **kwargs)
