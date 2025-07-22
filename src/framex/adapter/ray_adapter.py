from collections.abc import Callable
from typing import Any, cast

from fastapi import FastAPI
from ray import serve
from typing_extensions import override

from framex.adapter.base import AdapterMode, BaseAdapter
from framex.consts import APP_NAME


class RayAdapter(BaseAdapter):  # pragma: no cover
    mode = AdapterMode.RAY

    @override
    def to_ingress(self, cls: type, app: FastAPI, **kwargs: Any) -> type:
        cls = serve.ingress(app)(cls)
        return self.to_deployment(cls, **kwargs)

    @override
    def to_deployment(self, cls: type, **kwargs: Any) -> type:
        return cast(type, serve.deployment(**kwargs)(cls))

    @override
    def get_handle(self, deployment_name: str) -> Any:
        return serve.get_deployment_handle(deployment_name, app_name=APP_NAME)

    @override
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any:
        return deployment.bind(**kwargs)  # type: ignore [attr-defined]

    @override
    def _stream_call(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return func.options(stream=True).remote(**kwargs)  # type: ignore [attr-defined]

    @override
    async def _acall(self, func: Callable[..., Any], **kwargs: Any) -> Any:
        return await func.remote(**kwargs)  # type: ignore [attr-defined]
