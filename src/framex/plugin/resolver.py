from collections.abc import Mapping
from contextvars import ContextVar
from typing import Any

from framex.plugin.model import PluginApi


def coerce_plugin_api(api: PluginApi | dict[str, Any] | None) -> PluginApi | None:
    if api is None or isinstance(api, PluginApi):
        return api
    if isinstance(api, dict):
        return PluginApi.model_validate(api)
    return None


_current_remote_apis: ContextVar[Mapping[str, PluginApi | dict[str, Any]] | None] = ContextVar(
    "_current_remote_apis", default=None
)


def get_current_remote_apis() -> Mapping[str, PluginApi | dict[str, Any]] | None:
    return _current_remote_apis.get()


def set_current_remote_apis(remote_apis: Mapping[str, PluginApi | dict[str, Any]] | None) -> Any:
    return _current_remote_apis.set(remote_apis)


def reset_current_remote_apis(token: Any) -> None:
    _current_remote_apis.reset(token)
