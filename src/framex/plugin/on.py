import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from pydantic import BaseModel
from ray import serve

from framex.consts import API_STR
from framex.plugin.model import ApiType, PluginApi, PluginDeployment
from framex.utils import extract_method_params, plugin_to_deployment_name

from . import _current_plugin


def on_register(**kwargs: Any) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
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
                            tags=[plugin.name],
                            stream=func.__expose_stream,
                        )
                    )

            cls = serve.deployment(**kwargs)(cls)
            deployment = PluginDeployment(plugin_apis=plugin_apis, deployment=cls)
            plugin.deployments.append(deployment)

            # logger.opt(colors=True).debug(
            #     f'Found deploment "<m>{escape_tag(kwargs["name"])}</m> " from {plugin.module_name}'
            # )

        return cls

    return decorator


def on_request(
    path: str | None = None, methods: list[str] | None = None, call_type: ApiType = ApiType.HTTP, stream: bool = False
) -> Callable:
    if methods is None:
        methods = ["GET"]

    if call_type == ApiType.PROXY:
        raise TypeError("@on_request() does not support PROXY call_type")

    def wrapper(func: Callable) -> Callable:
        type_hints = get_type_hints(func, include_extras=True)
        sig = inspect.signature(func)

        base_model_params = [
            name
            for name in sig.parameters
            if name != "self" and isinstance(type_hints.get(name), type) and issubclass(type_hints[name], BaseModel)
        ]

        if len(base_model_params) > 1:
            raise TypeError(
                f"@on_request({path!r}) allows only one BaseModel parameter, "
                "but found {len(base_model_params)}: {base_model_params}"
            )

        if not path and call_type in [ApiType.HTTP, ApiType.ALL]:
            raise TypeError(f"@on_request({path!r}) requires a path when call_type is {call_type}")

        func._on_request = True  # type: ignore [attr-defined]
        func.__expose_path__ = path  # type: ignore [attr-defined]
        func.__expose_methods_ = methods  # type: ignore [attr-defined]
        func.__expose__call_type = call_type  # type: ignore [attr-defined]
        func.__expose_stream = stream  # type: ignore [attr-defined]
        return func

    return wrapper
