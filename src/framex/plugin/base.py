from typing import Any, final

from pydantic import BaseModel

from framex.adapter import get_adapter
from framex.config import settings
from framex.log import setup_logger
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
        if not (api := self.remote_apis.get(api_name)):  # pragma: no cover
            raise RuntimeError(
                f"API {api_name} is not in `required_remote_apis` by this plugin, "
                f"current plugins: {self.remote_apis.keys()}"
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
                except Exception as e:  # pragma: no cover
                    raise RuntimeError(f"Failed to convert '{key}' to {expected_type}") from e
        return await get_adapter().call_func(api, **kwargs)
