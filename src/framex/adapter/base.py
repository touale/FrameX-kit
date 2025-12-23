import abc
import inspect
from collections.abc import Callable
from enum import StrEnum
from typing import Any, cast

from aiocache import Cache, cached
from fastapi import FastAPI
from ray.serve.handle import DeploymentHandle

from framex.consts import PROXY_PLUGIN_NAME
from framex.plugin.model import ApiType, PluginApi


class AdapterMode(StrEnum):
    LOCAL = "noray"
    RAY = "ray"


class BaseAdapter(abc.ABC):
    mode: AdapterMode

    def to_ingress(self, cls: type, app: FastAPI, **kwargs: Any) -> type:  # noqa: ARG002
        return cls

    def to_deployment(self, cls: type, **kwargs: Any) -> type:  # noqa: ARG002
        return cls

    async def call_func(self, api: PluginApi, **kwargs: Any) -> Any:
        func = self.get_handle_func(api.deployment_name, api.func_name)
        stream = api.stream
        if api.call_type == ApiType.PROXY and api.api:
            kwargs["proxy_path"] = api.api
            stream = await self._check_is_gen_api(api.api)
        if stream:
            return [chunk async for chunk in self._stream_call(func, **kwargs)]
        if inspect.iscoroutinefunction(func) or isinstance(func, DeploymentHandle):
            return await self._acall(func, **kwargs)  # type: ignore
        return self._call(func, **kwargs)

    def get_handle_func(self, deployment_name: str, func_name: str) -> Any:
        handle = self.get_handle(deployment_name)
        if handle and (func := getattr(handle, func_name)):
            return func
        raise RuntimeError(f"No handle or function found for deployment({deployment_name}:{func_name})")

    @cached(cache=Cache.MEMORY)
    async def _check_is_gen_api(self, path: str) -> bool:
        func = self.get_handle_func(PROXY_PLUGIN_NAME, "check_is_gen_api")
        return cast(bool, await self._acall(func, path=path))

    @abc.abstractmethod
    def get_handle(self, deployment_name: str) -> Any: ...

    @abc.abstractmethod
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any: ...

    @abc.abstractmethod
    def to_remote_func(self, func: Callable) -> Callable: ...

    def _stream_call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func(**kwargs)

    async def _acall(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return await func(**kwargs)

    def _call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func(**kwargs)
