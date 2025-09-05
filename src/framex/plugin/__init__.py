from contextvars import ContextVar
from typing import Any, Optional

from pydantic import BaseModel
from ray.serve.handle import DeploymentHandle

from framex.adapter import get_adapter
from framex.config import settings
from framex.consts import PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin.manage import PluginManager
from framex.plugin.model import Plugin, PluginApi

_manager: PluginManager = PluginManager(silent=settings.test.silent)

_current_plugin: ContextVar[Optional["Plugin"]] = ContextVar("_current_plugin", default=None)


def get_plugin(plugin_id: str) -> Plugin | None:
    return _manager._plugins.get(plugin_id)


def get_loaded_plugins() -> set["Plugin"]:
    return set(_manager._plugins.values())


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
                dep.deployment, remote_apis=remote_apis, config=plugin.config, data_dir=plugin.data_dir
            )

            deployments.append(deployment)

    return deployments


async def call_plugin_api(
    api_name: str,
    interval_apis: dict[str, PluginApi] | None = None,
    **kwargs: Any,
) -> Any:
    api = interval_apis.get(api_name) if interval_apis else _manager.get_api(api_name)
    if not api:
        if api_name.startswith("/") and settings.server.enable_proxy:
            api = PluginApi(
                api=api_name,
                deployment_name=PROXY_PLUGIN_NAME,
                call_type=ApiType.PROXY,
            )
            logger.opt(colors=True).warning(
                f"Api(<r>{api_name}</r>) not found, use proxy plugin({PROXY_PLUGIN_NAME}) to transfer!"
            )
        else:
            raise RuntimeError(
                f"API {api_name} is not found, please check if the plugin is loaded or the API name is correct."
            )
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
    return await get_adapter().call_func(api, **kwargs)


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
