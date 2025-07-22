from contextvars import ContextVar
from typing import Optional

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
                        plugin_name=PROXY_PLUGIN_NAME,
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
            deployment = get_adapter().bind(dep.deployment, remote_apis=remote_apis, config=plugin.config)

            deployments.append(deployment)

    return deployments


def get_http_plugin_apis() -> list["PluginApi"]:
    return _manager.http_plugin_apis


from .base import BasePlugin
from .load import load_builtin_plugin, load_plugins
from .model import ApiType, PluginMetadata
from .on import on_register, on_request

__all__ = [
    "ApiType",
    "BasePlugin",
    "PluginMetadata",
    "load_builtin_plugin",
    "load_plugins",
    "on_register",
    "on_request",
]
