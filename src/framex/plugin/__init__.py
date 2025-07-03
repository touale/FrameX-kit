# _managers: "PluginManager" = []


from contextvars import ContextVar
from typing import Optional

from ray import serve
from ray.serve.handle import DeploymentHandle

from framex.consts import APP_NAME
from framex.plugin.manage import PluginManager
from framex.plugin.model import Plugin, PluginApi

_manager: PluginManager = PluginManager()

_current_plugin: ContextVar[Optional["Plugin"]] = ContextVar("_current_plugin", default=None)


def get_loaded_plugins() -> set["Plugin"]:
    return set(_manager._plugins.values())


def get_all_deployments() -> list[DeploymentHandle]:
    deployments = []
    for plugin in get_loaded_plugins():
        for dep in plugin.deployments:
            remote_apis = {
                plugin_name: api
                for plugin_name in plugin.required_remote_apis
                if (api := _manager.get_api(plugin_name))
            }
            deployments.append(dep.deployment.bind(remote_apis=remote_apis))

    return deployments


def get_http_plugin_apis() -> list["PluginApi"]:
    return _manager.http_plugin_apis


async def call_remote_api(api: PluginApi, **kwargs):
    handle: DeploymentHandle = serve.get_deployment_handle(api.deployment_name, app_name=APP_NAME)
    c_handle = getattr(handle, api.func_name)
    if not c_handle:
        raise RuntimeError(f"No handle found for func_name({api.func_name})")

    return await c_handle.remote(**kwargs)


from .base import BasePlugin
from .load import load_builtin_plugin, load_plugins
from .model import ApiType, PluginApi, PluginMetadata
from .on import on_register, on_request

__all__ = [
    "ApiType",
    "BasePlugin",
    "PluginApi",
    "PluginMetadata",
    "load_builtin_plugin",
    "load_plugins",
    "on_register",
    "on_request",
]
