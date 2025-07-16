from collections.abc import Callable
from typing import Any, cast

from aiocache import Cache, cached
from fastapi import FastAPI
from ray import serve
from typing_extensions import override

from framex.adapter.base import AdapterMode, BaseAdapter
from framex.consts import APP_NAME, PROXY_PLUGIN_NAME
from framex.plugin.model import ApiType, PluginApi


class RayAdapter(BaseAdapter):
    mode = AdapterMode.RAY

    @override
    def to_ingress(self, cls: type, app: FastAPI, **kwargs: Any) -> type:
        cls = serve.ingress(app)(cls)
        return self.to_deployment(cls, **kwargs)

    @override
    def to_deployment(self, cls: type, **kwargs: Any) -> type:
        return cast(type, serve.deployment(**kwargs)(cls))

    @override
    async def call_func(self, api: PluginApi, **kwargs: Any) -> Any:
        func = self.get_handle_func(api.deployment_name, api.func_name)
        stream = api.stream

        if api.call_type == ApiType.PROXY:
            kwargs["proxy_path"] = api.api
            stream = await self._check_is_gen_api(api.api)

        if stream:
            return [chunk async for chunk in self._stream_call(func, **kwargs)]

        res = await self._acall(func, **kwargs)
        return data if api.call_type == ApiType.PROXY and (data := res.get("data")) else res

    @override
    def get_handle(self, deployment_name: str) -> Any:
        return serve.get_deployment_handle(deployment_name, app_name=APP_NAME)

    @cached(cache=Cache.MEMORY)
    @override
    async def _check_is_gen_api(self, path: str) -> bool:
        func = self.get_handle_func(PROXY_PLUGIN_NAME, "check_is_gen_api")
        return cast(bool, await self._acall(func, path=path))

    @override
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any:
        return deployment.bind(**kwargs)  # type: ignore [attr-defined]

    @override
    def _stream_call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func.options(stream=True).remote(**kwargs)  # type: ignore [attr-defined]

    @override
    async def _acall(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return await func.remote(**kwargs)  # type: ignore [attr-defined]
