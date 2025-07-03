import inspect
from typing import get_type_hints

from pydantic import BaseModel
from ray import serve

from framex.consts import API_STR
from framex.log import logger
from framex.plugin.model import ApiType, PluginApi, PluginDeployment
from framex.utils import escape_tag, extract_method_params, plugin_to_deployment_name

from . import _current_plugin


def on_register(**kwargs):
    def decorator(cls):
        if plugin := _current_plugin.get():
            tag = plugin_to_deployment_name(
                plugin.name,
                cls.__name__,
            )
            kwargs.setdefault("name", tag)

            plugin_apis = []

            for name, func in inspect.getmembers(cls):
                if getattr(func, "_on_request", False):
                    call_type = func.__expose__call_type
                    path = func.__expose_path__

                    if not path:
                        call_type = ApiType.FUNC
                    elif not path.startswith(API_STR):
                        path = f"{API_STR}{path}" if path.startswith("/") else f"{API_STR}/{path}"

                    params = extract_method_params(func)
                    plugin_apis.append(
                        PluginApi(
                            api=path,
                            deployment_name=tag,
                            func_name=name,
                            methods=func.__expose_methods_,
                            params=params,
                            call_type=call_type,
                        )
                    )

            cls = serve.deployment(**kwargs)(cls)
            deployment = PluginDeployment(plugin_apis=plugin_apis, deployment=cls)
            plugin.deployments.append(deployment)

            logger.opt(colors=True).debug(
                f'Found deploment "<m>{escape_tag(kwargs["name"])}</m> " from {plugin.module_name}'
            )

        return cls

    return decorator


def on_request(
    path: str | None = None,
    methods: list[str] = ["GET"],
    call_type: ApiType = ApiType.ALL,
):
    def wrapper(func):
        type_hints = get_type_hints(func, include_extras=True)
        sig = inspect.signature(func)

        base_model_params = [
            name
            for name in sig.parameters.keys()
            if name != "self" and isinstance(type_hints.get(name), type) and issubclass(type_hints[name], BaseModel)
        ]

        if len(base_model_params) > 1:
            raise TypeError(
                f"@on_request({path!r}) allows only one BaseModel parameter, but found {len(base_model_params)}: {base_model_params}"
            )

        if not path and call_type in [ApiType.HTTP, ApiType.ALL]:
            raise TypeError(f"@on_request({path!r}) requires a path when call_type is {call_type}")

        func._on_request = True
        func.__expose_path__ = path
        func.__expose_methods_ = methods
        func.__expose__call_type = call_type
        return func

    return wrapper
