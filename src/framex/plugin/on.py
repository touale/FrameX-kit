import functools
import inspect
import types
from collections.abc import Callable
from typing import Any, get_type_hints

from pydantic import BaseModel

from framex.adapter import get_adapter
from framex.consts import API_STR, PROXY_PLUGIN_NAME
from framex.plugin.model import ApiType, PluginApi, PluginDeployment
from framex.utils import cache_decode, cache_encode, extract_method_params, plugin_to_deployment_name

from . import _current_plugin, call_plugin_api


def on_register(**kwargs: Any) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        if plugin := _current_plugin.get():
            tag = plugin_to_deployment_name(
                plugin.name,
                cls.__name__,
            )
            kwargs.setdefault("name", tag)

            plugin_apis = []

            for name, func in inspect.getmembers(object=cls):
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
                            tags=[plugin.name + "(v" + plugin.module.__plugin_meta__.version + ")"],
                            stream=func.__expose_stream,
                        )
                    )
            from framex.config import settings

            merge_kwargs = {**settings.base_ingress_config, **kwargs}
            cls = get_adapter().to_deployment(cls, **merge_kwargs)
            deployment = PluginDeployment(plugin_apis=plugin_apis, deployment=cls)
            plugin.deployments.append(deployment)

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


def on_proxy() -> Callable:
    def decorator(func: Callable) -> Callable:
        from framex.config import settings

        if not settings.server.enable_proxy:  # pragma: no cover
            return func

        is_registered = False
        full_func_name = f"{func.__module__}.{func.__name__}"

        async def safe_callable(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception:
                raw = func

                if isinstance(raw, (classmethod, staticmethod)):
                    raw = raw.__func__

                while hasattr(raw, "__wrapped__"):
                    raw = raw.__wrapped__

                if inspect.iscoroutinefunction(raw):
                    return await raw(*args, **kwargs)
                return raw(*args, **kwargs)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal is_registered

            if args:  # pragma: no cover
                raise TypeError(f"The proxy function '{func.__name__}' only supports keyword arguments.")

            if not is_registered:
                api_reg = PluginApi(
                    deployment_name=PROXY_PLUGIN_NAME,
                    call_type=ApiType.PROXY,
                    func_name="register_proxy_function",
                )
                await call_plugin_api(
                    api_reg,
                    None,
                    func_name=full_func_name,
                    func_callable=safe_callable,
                )
                is_registered = True

            api_call = PluginApi(
                deployment_name=PROXY_PLUGIN_NAME,
                call_type=ApiType.PROXY,
                func_name="call_proxy_function",
            )
            res = await call_plugin_api(
                api_call,
                None,
                func_name=cache_encode(full_func_name),
                data=cache_encode(data=kwargs),
            )
            return cache_decode(res)

        return wrapper

    return decorator


def remote() -> Callable:
    def wrapper(func: Callable) -> Any:
        adapter = get_adapter()

        # If it is a classmethod, unpack it to the original function in advance
        is_cm = isinstance(func, classmethod)
        orig_func = func.__func__ if is_cm else func  # type: ignore[attr-defined]

        class RemoteCallable:
            """A wrapper that supports both direct and .remote() asynchronous calls"""

            def __init__(self, bound_func: Callable, bound_remote: Callable):
                self._func = bound_func
                self.remote = bound_remote

            def __call__(self, *args: Any, **kwargs: Any):
                return self._func(*args, **kwargs)

        class RemoteInstanceDescriptor:
            """Instance method descriptors: bind self to .remote(self, ...)"""

            __func__ = None  # Avoid being treated as a field by Pydantic

            def __get__(self, instance: Any | None, owner: type[Any]):
                if instance is None:
                    return orig_func
                wrapped = adapter.to_remote_func(orig_func)
                bound_func = types.MethodType(wrapped, instance)
                bound_remote = types.MethodType(wrapped.remote, instance)  # type: ignore[attr-defined]
                return RemoteCallable(bound_func, bound_remote)

        class RemoteClassDescriptor:
            """Class method descriptor: bind cls to .remote(cls, ...)"""

            __func__ = None  # Avoid being treated as a field by Pydantic

            def __get__(self, instance: Any | None, owner: type[Any]) -> RemoteCallable:
                # Here we explicitly use owner for binding, ensuring that .remote is also bound to cls
                wrapped = adapter.to_remote_func(orig_func)
                bound_func = types.MethodType(wrapped, owner)
                bound_remote = types.MethodType(wrapped.remote, owner)  # type: ignore[attr-defined]
                return RemoteCallable(bound_func, bound_remote)

        # —— Determine function type (do not rely on __code__, avoid RemoteFunction and other packaging) ——
        try:
            params = list(inspect.signature(orig_func).parameters)
        except (TypeError, ValueError):
            params = []

        # Class method: explicit @classmethod or first parameter named cls
        if is_cm or (params and params[0] == "cls"):
            return RemoteClassDescriptor()

        # Instance method: the first parameter is named self
        if params and params[0] == "self":
            return RemoteInstanceDescriptor()

        # Normal function: directly passed to the adapter and returns a function object with .remote
        return adapter.to_remote_func(orig_func)

    return wrapper
