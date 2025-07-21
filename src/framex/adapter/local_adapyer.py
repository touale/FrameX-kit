from collections.abc import Callable
from typing import Any

from typing_extensions import override

from framex.adapter.base import AdapterMode, BaseAdapter
from framex.consts import BACKEND_NAME


class LocalAdapter(BaseAdapter):
    mode = AdapterMode.LOCAL

    @override
    def to_deployment(self, cls: type, **kwargs: Any) -> type:
        if tag := kwargs.get("name"):
            setattr(cls, "deployment_name", tag)
        return super().to_deployment(cls, **kwargs)

    @override
    def get_handle(self, deployment_name: str) -> Any:
        from framex.driver.ingress import app

        return (
            app.state.deployments_dict.get(deployment_name) if deployment_name != BACKEND_NAME else app.state.ingress
        )

    @override
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any:
        return deployment(**kwargs)
