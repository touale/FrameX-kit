from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from framex.adapter import get_adapter


def api_ingress(*, app: FastAPI, **kwargs: Any) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        if not isinstance(cls, type):  # pragma: no cover
            raise TypeError("api_ingress must be used to decorate a class.")
        from framex.config import settings

        merge_kwargs = {**settings.base_ingress_config, **settings.server.ingress_config, **kwargs}
        return get_adapter().to_ingress(cls, app, **merge_kwargs)

    return decorator
