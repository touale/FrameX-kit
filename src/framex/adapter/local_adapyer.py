from collections.abc import Callable
from typing import Any, cast

from aiocache import Cache, cached

from framex.adapter.base import AdapterMode, BaseAdapter
from framex.consts import BACKEND_NAME, PROXY_PLUGIN_NAME
from framex.plugin.model import ApiType, PluginApi


class LocalAdapter(BaseAdapter):
    def __init__(self):
        return super().__init__(AdapterMode.LOCAL)

    def to_deployment(self, cls: type, **kwargs: Any) -> type:
        if tag := kwargs.get("name"):
            setattr(cls, "deployment_name", tag)
        return cls

    async def call_func(self, api: PluginApi, **kwargs: Any) -> Any:
        func = self.get_handle_func(api.deployment_name, api.func_name)
        stream = api.stream

        if api.call_type == ApiType.PROXY:
            kwargs["proxy_path"] = api.api
            stream = await self._check_is_gen_api(api.api)

        if stream:
            return [chunk async for chunk in self._stream_call(func, **kwargs)]

        if func.__module__ == "framex.driver.ingress" and func.__name__ == "register_route":
            # Only banckend can be call with sync func!
            res = self._call(func, **kwargs)
        else:
            res = await self._acall(func, **kwargs)

        return data if api.call_type == ApiType.PROXY and (data := res.get("data")) else res

    def get_handle(self, deployment_name: str) -> Any:
        from framex.driver.ingress import app

        return (
            app.state.deployments_dict.get(deployment_name) if deployment_name != BACKEND_NAME else app.state.ingress
        )

    @cached(cache=Cache.MEMORY)
    async def _check_is_gen_api(self, path: str) -> bool:
        func = self.get_handle_func(PROXY_PLUGIN_NAME, "check_is_gen_api")
        return cast(bool, await func(path=path))

    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any:
        return deployment(**kwargs)
