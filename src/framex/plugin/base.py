import inspect
from collections.abc import Mapping
from functools import wraps
from typing import Any, final

from framex.config import settings
from framex.log import setup_logger
from framex.plugin import (
    ApiResolver,
    call_plugin_api,
    reset_current_api_resolver,
    reset_current_remote_apis,
    set_current_api_resolver,
    set_current_remote_apis,
)
from framex.plugin.model import PluginApi


class BasePlugin:
    """Base class for all plugins"""

    def __init__(self, **kwargs: Any) -> None:
        setup_logger()
        self.remote_apis: dict[str, PluginApi] = kwargs.get("remote_apis", {})
        self.api_registry: Mapping[str, PluginApi] = kwargs.get("api_registry", {})
        self.api_resolver = ApiResolver(api_registry=self.api_registry)
        self._bind_api_resolver_context()
        if settings.server.use_ray:
            import asyncio

            asyncio.create_task(self.on_start())  # noqa: RUF006

    async def on_start(self) -> None:
        pass

    def _bind_api_resolver_context(self) -> None:
        for name, func in inspect.getmembers(type(self), predicate=callable):
            if not getattr(func, "_on_request", False):
                continue
            bound = getattr(self, name)
            setattr(self, name, self._wrap_with_api_resolver(bound))

    def _wrap_with_api_resolver(self, func: Any) -> Any:
        if inspect.isasyncgenfunction(func):

            @wraps(func)
            async def async_gen_wrapper(*args: Any, **kwargs: Any) -> Any:
                resolver_token = set_current_api_resolver(self.api_resolver)
                remote_token = set_current_remote_apis(self.remote_apis)
                try:
                    async for chunk in func(*args, **kwargs):
                        yield chunk
                finally:
                    reset_current_remote_apis(remote_token)
                    reset_current_api_resolver(resolver_token)

            return async_gen_wrapper

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                resolver_token = set_current_api_resolver(self.api_resolver)
                remote_token = set_current_remote_apis(self.remote_apis)
                try:
                    return await func(*args, **kwargs)
                finally:
                    reset_current_remote_apis(remote_token)
                    reset_current_api_resolver(resolver_token)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            resolver_token = set_current_api_resolver(self.api_resolver)
            remote_token = set_current_remote_apis(self.remote_apis)
            try:
                return func(*args, **kwargs)
            finally:
                reset_current_remote_apis(remote_token)
                reset_current_api_resolver(resolver_token)

        return sync_wrapper

    @final
    async def _call_remote_api(self, api_name: str, **kwargs: Any) -> Any:
        res = await call_plugin_api(api_name, **kwargs)
        return self._post_call_remote_api_hook(res)

    def _post_call_remote_api_hook(self, data: Any) -> Any:
        return data
