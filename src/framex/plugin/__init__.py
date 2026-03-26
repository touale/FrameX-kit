from contextvars import ContextVar
from functools import lru_cache
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from framex.adapter import get_adapter
from framex.config import settings
from framex.consts import PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin.manage import _manager
from framex.plugin.model import Plugin, PluginApi
from framex.plugin.resolver import (
    ApiResolver,
    _set_default_api_resolver,
    get_current_api_resolver,
    get_current_remote_apis,
    get_default_api_resolver,
)

C = TypeVar("C", bound=BaseModel)

_current_plugin: ContextVar[Optional["Plugin"]] = ContextVar("_current_plugin", default=None)
_set_default_api_resolver(ApiResolver(manager=_manager))


def get_plugin(plugin_id: str) -> Plugin | None:
    return _manager._plugins.get(plugin_id)


def get_loaded_plugins() -> set["Plugin"]:
    return set(_manager._plugins.values())


@lru_cache
def get_plugin_config(plugin_name: str, config_class: type[C]) -> C:
    if cfg := settings.plugins.get(plugin_name):
        return config_class(**cfg)
    logger.warning(f"Plugin({plugin_name}) config not found, use default config")
    return config_class()


def check_plugin_config_exists(plugin_name: str) -> bool:
    return plugin_name in settings.plugins


@logger.catch()
def init_all_deployments(enable_proxy: bool) -> list[Any]:
    deployments = []
    all_apis = {**_manager.all_plugin_apis[ApiType.FUNC], **_manager.all_plugin_apis[ApiType.HTTP]}
    for plugin in get_loaded_plugins():
        for dep in plugin.deployments:
            remote_apis = {
                api_name: api for api_name in plugin.required_remote_apis if (api := _manager.get_api(api_name))
            }
            for api_name in plugin.required_remote_apis:
                if api_name in remote_apis:
                    continue
                if api_name.startswith("/") and enable_proxy:
                    remote_apis[api_name] = PluginApi(
                        api=api_name,
                        deployment_name=PROXY_PLUGIN_NAME,
                        call_type=ApiType.PROXY,
                    )
                    logger.opt(colors=True).warning(
                        f"Api(<r>{api_name}</r>) not found, "
                        f"plugin(<r>{dep.deployment}</r>) will "
                        f"use proxy plugin({PROXY_PLUGIN_NAME}) to transfer!"
                    )
                else:  # pragma: no cover
                    raise RuntimeError(
                        f"Plugin({dep.deployment}) init failed, Required remote api({api_name}) not found"
                    )
            deployment = get_adapter().bind(
                dep.deployment,
                remote_apis=remote_apis,
                api_registry=all_apis,
                config=plugin.config,
            )

            deployments.append(deployment)

    return deployments


def _resolve_plugin_api(
    api_name: str | PluginApi,
    resolver: ApiResolver | None = None,
) -> tuple[PluginApi, bool]:
    current_remote_apis = get_current_remote_apis()
    if isinstance(api_name, PluginApi):
        return api_name, api_name.call_type == ApiType.PROXY

    active_resolver = resolver or get_current_api_resolver() or get_default_api_resolver()
    if current_remote_apis is not None:
        api = active_resolver.coerce_plugin_api(current_remote_apis.get(api_name))
    else:
        api = active_resolver.resolve(api_name, None)

    if api is None:
        if current_remote_apis is not None:
            raise RuntimeError(
                f"API {api_name} is not declared in current plugin remote_apis; add it to required_remote_apis."
            )
        if api_name.startswith("/") and settings.server.enable_proxy:
            api = PluginApi(
                api=api_name,
                deployment_name=PROXY_PLUGIN_NAME,
                call_type=ApiType.PROXY,
            )
            logger.opt(colors=True).warning(
                f"Api(<y>{api_name}</y>) not found, use proxy plugin({PROXY_PLUGIN_NAME}) to transfer!"
            )
        else:
            raise RuntimeError(
                f"API {api_name} is not found, please check if the plugin is loaded or the API name is correct."
            )

    return api, api.call_type == ApiType.PROXY


def _normalize_plugin_call_kwargs(api: PluginApi, kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized_kwargs = dict(kwargs)
    param_type_map = dict(api.params)
    for key, val in normalized_kwargs.items():
        if (
            isinstance(val, dict)
            and (expected_type := param_type_map.get(key))
            and isinstance(expected_type, type)
            and issubclass(expected_type, BaseModel)
        ):
            try:
                normalized_kwargs[key] = expected_type(**val)
            except Exception as e:  # pragma: no cover
                raise RuntimeError(f"Failed to convert '{key}' to {expected_type}") from e
    return normalized_kwargs


def _unwrap_plugin_call_result(api_name: str | PluginApi, result: Any, use_proxy: bool) -> Any:
    if isinstance(result, BaseModel):
        return result.model_dump(by_alias=True)
    if not use_proxy:
        return result
    if not isinstance(result, dict):
        return result
    if "status" not in result:
        raise RuntimeError(f"Proxy API {api_name} returned invalid response: missing 'status' field")

    res = result.get("data")
    status = result.get("status")
    if status not in settings.server.legal_proxy_code:
        logger.opt(colors=True).error(f"<>Proxy API {api_name} call illegal: <r>{result}</r>")
        raise RuntimeError(f"Proxy API {api_name} returned status {status}")
    if res is None:
        logger.opt(colors=True).warning(f"API {api_name} returned empty data")
    return res


async def call_plugin_api(
    api_name: str | PluginApi,
    resolver: ApiResolver | None = None,
    **kwargs: Any,
) -> Any:
    api, use_proxy = _resolve_plugin_api(api_name, resolver=resolver)
    normalized_kwargs = _normalize_plugin_call_kwargs(api, kwargs)
    result = await get_adapter().call_func(api, **normalized_kwargs)
    return _unwrap_plugin_call_result(api_name, result, use_proxy)


def get_http_plugin_apis() -> list["PluginApi"]:
    return _manager.http_plugin_apis


from .base import BasePlugin
from .load import load_builtin_plugins, load_plugins, register_proxy_func
from .model import ApiType, PluginMetadata
from .on import on_proxy, on_register, on_request, remote

__all__ = [
    "ApiType",
    "BasePlugin",
    "PluginMetadata",
    "load_builtin_plugins",
    "load_plugins",
    "on_proxy",
    "on_register",
    "on_request",
    "register_proxy_func",
    "remote",
]
