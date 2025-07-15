from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from ray import serve

from framex.config import settings


def api_ingress(*, app: FastAPI, **kwargs: Any) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        if not isinstance(cls, type):
            raise TypeError("api_ingress must be used to decorate a class.")

        if settings.server.use_ray:
            cls = serve.ingress(app)(cls)
            cls = serve.deployment(**kwargs)(cls)

        return cls

    return decorator
