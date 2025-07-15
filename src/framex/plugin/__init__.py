from contextvars import ContextVar
from typing import Any, Optional, cast

from aiocache import Cache, cached
from ray import serve
from ray.serve.handle import DeploymentHandle

from framex.config import settings
from framex.consts import APP_NAME, BACKEND_NAME, PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin.manage import PluginManager
from framex.plugin.model import Plugin, PluginApi

_manager: PluginManager = PluginManager()

_current_plugin: ContextVar[Optional["Plugin"]] = ContextVar("_current_plugin", default=None)


def get_loaded_plugins() -> set["Plugin"]:
    return set(_manager._plugins.values())


@logger.catch()
def init_all_deployments() -> list[DeploymentHandle]:
    deployments = []
    for plugin in get_loaded_plugins():
        for dep in plugin.deployments:
            remote_apis = {
                api_name: api for api_name in plugin.required_remote_apis if (api := _manager.get_api(api_name))
            }
            for api_name in plugin.required_remote_apis:
                if api_name in remote_apis:
                    continue

                if api_name.startswith("/") and settings.enable_proxy:
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
                else:
                    raise RuntimeError(
                        f"Plugin({dep.deployment}) init failed, Required remote api({api_name}) not found"
                    )
            if settings.server.use_ray:
                deployment = dep.deployment.bind(remote_apis=remote_apis, config=plugin.config)
            else:
                deployment = dep.deployment(remote_apis=remote_apis, config=plugin.config)

            deployments.append(deployment)

    return deployments


def get_http_plugin_apis() -> list["PluginApi"]:
    return _manager.http_plugin_apis


@cached(cache=Cache.MEMORY)
async def _check_is_gen_api(path: str) -> bool:
    handle_func = await _get_handle_func(PROXY_PLUGIN_NAME, "check_is_gen_api")
    if settings.server.use_ray:
        return cast(bool, await handle_func.remote(path=path))
    return cast(bool, await handle_func(path=path))


async def _get_handle_func(deployment_name: str, func_name: str) -> Any:
    if settings.server.use_ray:
        handle = serve.get_deployment_handle(deployment_name, app_name=APP_NAME)
    else:
        from framex.driver.ingress import app

        handle = (
            app.state.deployments_dict.get(deployment_name) if deployment_name != BACKEND_NAME else app.state.ingress
        )

    if not handle or not (handle_func := getattr(handle, func_name)):
        raise RuntimeError(f"No handle found for func_name({func_name})")

    return handle_func


async def call_remote_api(api: PluginApi, **kwargs: Any) -> Any:
    c_handle = await _get_handle_func(api.deployment_name, api.func_name)

    stream = api.stream

    if api.call_type == ApiType.PROXY:
        kwargs["proxy_path"] = api.api
        stream = await _check_is_gen_api(api.api)

    if stream:
        if settings.server.use_ray:
            c_handle = c_handle.options(stream=True).remote
        gen = c_handle(**kwargs)
        return [chunk async for chunk in gen]

    if settings.server.use_ray:
        res = await c_handle.remote(**kwargs)
    elif c_handle.__module__ == "framex.driver.ingress" and c_handle.__name__ == "register_route":
        # Only banckend can be call with sync func!
        res = c_handle(**kwargs)
    else:
        res = await c_handle(**kwargs)

    return data if api.call_type == ApiType.PROXY and (data := res.get("data")) else res


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
