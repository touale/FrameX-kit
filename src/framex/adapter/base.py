import abc
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from fastapi import FastAPI

from framex.plugin.model import PluginApi


class AdapterMode(StrEnum):
    LOCAL = "local"
    RAY = "ray"


class BaseAdapter(abc.ABC):
    def __init__(self, mode: AdapterMode):
        self.mode = mode

    def to_ingress(self, cls: type, app: FastAPI, **kwargs: Any) -> type:  # noqa: ARG002
        return cls

    def to_deployment(self, cls: type, **kwargs: Any) -> type:  # noqa: ARG002
        return cls

    @abc.abstractmethod
    async def call_func(self, api: PluginApi, **kwargs: Any) -> Any: ...

    @abc.abstractmethod
    def get_handle(self, deployment_name: str) -> Any: ...

    def get_handle_func(self, deployment_name: str, func_name: str) -> Any:
        handle = self.get_handle(deployment_name)
        if handle and (func := getattr(handle, func_name)):
            return func
        raise RuntimeError(f"No handle or function found for deployment({deployment_name}:{func_name})")

    @abc.abstractmethod
    async def _check_is_gen_api(self, path: str) -> Any: ...

    @abc.abstractmethod
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any: ...

    def _stream_call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func(**kwargs)

    async def _acall(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return await func(**kwargs)

    def _call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func(**kwargs)
