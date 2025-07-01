import inspect

from ray import serve

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

                    if not func.__expose_path__:
                        call_type = ApiType.FUNC

                    params = extract_method_params(func)

                    plugin_apis.append(
                        PluginApi(
                            api=func.__expose_path__,
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

            logger.opt(colors=True).success(
                f'Found deploment "<y>{escape_tag(kwargs["name"])}</y>"'
                + (f' from "<m>{escape_tag(plugin.module_name)}</m>"' if plugin.module_name != plugin.name else "")
            )

        return cls

    return decorator


def on_request(
    path: str | None = None,
    methods: list[str] = ["GET"],
    call_type: ApiType = ApiType.ALL,
):
    def wrapper(func):
        func._on_request = True

        func.__expose_path__ = path
        func.__expose_methods_ = methods
        func.__expose__call_type = call_type
        return func

    return wrapper
