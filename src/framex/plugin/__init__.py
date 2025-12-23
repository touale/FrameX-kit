from contextvars import ContextVar
from functools import lru_cache
from typing import Any, Optional, TypeVar

from pydantic import BaseModel
from ray.serve.handle import DeploymentHandle

from framex.adapter import get_adapter
from framex.config import settings
from framex.consts import PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin.manage import PluginManager
from framex.plugin.model import Plugin, PluginApi

C = TypeVar("C", bound=BaseModel)
_manager: PluginManager = PluginManager(silent=settings.test.silent)

_current_plugin: ContextVar[Optional["Plugin"]] = ContextVar("_current_plugin", default=None)


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
def init_all_deployments(enable_proxy: bool) -> list[DeploymentHandle]:
    deployments = []
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
                config=plugin.config,
            )

            deployments.append(deployment)

    return deployments


async def call_plugin_api(
    api_name: str | PluginApi,
    interval_apis: dict[str, PluginApi] | None = None,
    **kwargs: Any,
) -> Any:
    if isinstance(api_name, PluginApi):
        api: PluginApi | None = api_name
    elif isinstance(api_name, str):
        api = interval_apis.get(api_name) if interval_apis else _manager.get_api(api_name)
    use_proxy = False
    if not api:
        if isinstance(api_name, str) and api_name.startswith("/") and settings.server.enable_proxy:
            api = PluginApi(
                api=api_name,
                deployment_name=PROXY_PLUGIN_NAME,
                call_type=ApiType.PROXY,
            )
            logger.opt(colors=True).warning(
                f"Api(<y>{api_name}</y>) not found, use proxy plugin({PROXY_PLUGIN_NAME}) to transfer!"
            )
            use_proxy = True
        else:
            raise RuntimeError(
                f"API {api_name} is not found, please check if the plugin is loaded or the API name is correct."
            )
    if api.call_type == ApiType.PROXY:
        use_proxy = True
    param_type_map = dict(api.params)
    for key, val in kwargs.items():
        if (
            isinstance(val, dict)
            and (expected_type := param_type_map.get(key))
            and isinstance(expected_type, type)
            and issubclass(expected_type, BaseModel)
        ):
            try:
                kwargs[key] = expected_type(**val)
            except Exception as e:  # pragma: no cover
                raise RuntimeError(f"Failed to convert '{key}' to {expected_type}") from e
    result = await get_adapter().call_func(api, **kwargs)
    if isinstance(result, BaseModel):
        return result.model_dump(by_alias=True)
    if use_proxy:
        if not isinstance(result, dict):
            return result
        if "status" not in result:
            raise RuntimeError(f"Proxy API {api_name} returned invalid response: missing 'status' field")
        res = result.get("data")
        status = result.get("status")
        if status not in settings.server.legal_proxy_code:
            logger.opt(colors=True).error(f"Proxy API {api_name} call illegal: <r>{result}</r>")
            raise RuntimeError(f"Proxy API {api_name} returned status {status}")
        if res is None:
            logger.opt(colors=True).warning(f"API {api_name} returned empty data")
        return res
    return result


def get_http_plugin_apis() -> list["PluginApi"]:
    return _manager.http_plugin_apis


from .base import BasePlugin
from .load import load_builtin_plugins, load_plugins
from .model import ApiType, PluginMetadata
from .on import on_register, on_request, remote

__all__ = [
    "ApiType",
    "BasePlugin",
    "PluginMetadata",
    "load_builtin_plugins",
    "load_plugins",
    "on_register",
    "on_request",
    "remote",
]
