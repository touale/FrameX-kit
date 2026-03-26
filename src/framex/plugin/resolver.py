from collections.abc import Mapping
from contextvars import ContextVar
from typing import Any, Protocol

from framex.plugin.model import PluginApi


class SupportsApiLookup(Protocol):
    def get_api(self, api_name: str) -> PluginApi | None: ...


class ApiResolver:
    def __init__(
        self,
        manager: SupportsApiLookup | None = None,
        api_registry: Mapping[str, PluginApi | dict[str, Any]] | None = None,
    ) -> None:
        self._manager = manager
        self._api_registry = api_registry or {}

    @staticmethod
    def coerce_plugin_api(api: PluginApi | dict[str, Any] | None) -> PluginApi | None:
        if api is None or isinstance(api, PluginApi):
            return api
        if isinstance(api, dict):
            return PluginApi.model_validate(api)
        return None

    def resolve(
        self,
        api_name: str,
        api_registry: Mapping[str, PluginApi | dict[str, Any]] | None = None,
    ) -> PluginApi | None:
        if api_registry is not None and (api := self.coerce_plugin_api(api_registry.get(api_name))):
            return api
        if self._manager and (api := self._manager.get_api(api_name)):
            return api
        return self.coerce_plugin_api(self._api_registry.get(api_name))


_current_api_resolver: ContextVar[ApiResolver | None] = ContextVar("_current_api_resolver", default=None)
_current_remote_apis: ContextVar[Mapping[str, PluginApi | dict[str, Any]] | None] = ContextVar(
    "_current_remote_apis", default=None
)
_default_api_resolver: ApiResolver | None = None


def get_current_api_resolver() -> ApiResolver | None:
    return _current_api_resolver.get()


def get_default_api_resolver() -> ApiResolver:
    if _default_api_resolver is None:
        raise RuntimeError("Default API resolver is not configured")
    return _default_api_resolver


def _set_default_api_resolver(resolver: ApiResolver) -> None:
    global _default_api_resolver
    _default_api_resolver = resolver


def set_current_api_resolver(resolver: ApiResolver | None) -> Any:
    return _current_api_resolver.set(resolver)


def reset_current_api_resolver(token: Any) -> None:
    _current_api_resolver.reset(token)


def get_current_remote_apis() -> Mapping[str, PluginApi | dict[str, Any]] | None:
    return _current_remote_apis.get()


def set_current_remote_apis(remote_apis: Mapping[str, PluginApi | dict[str, Any]] | None) -> Any:
    return _current_remote_apis.set(remote_apis)


def reset_current_remote_apis(token: Any) -> None:
    _current_remote_apis.reset(token)
