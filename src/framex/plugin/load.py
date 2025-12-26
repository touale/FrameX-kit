from collections.abc import Callable

from framex.consts import PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin.model import ApiType, Plugin, PluginApi
from framex.plugin.on import _PROXY_REGISTRY

from . import _manager, call_plugin_api, get_loaded_plugins


def load_plugins(*plugin_dir: str) -> set[Plugin]:
    return _manager.load_plugins(plugin_dir)


def load_builtin_plugins(*names: str) -> set[Plugin]:
    return load_plugins(*[f"framex.plugins.{name}" for name in names])


@logger.catch(reraise=True)
def auto_load_plugins(builtin_plugins: list[str], plugins: list[str], enable_proxy: bool = False) -> set[Plugin]:
    # Get all builtin_plugins
    loaded_builtin_plugins = {
        plugin.name for plugin in get_loaded_plugins() if plugin.module_name.startswith("framex.plugins.")
    }
    # Candidate builtin_plugins
    candidate_builtin_plugins = set(builtin_plugins) - loaded_builtin_plugins
    # Check if proxy is enabled but not allow to load
    if (
        enable_proxy and "proxy" not in loaded_builtin_plugins and "proxy" not in candidate_builtin_plugins
    ):  # pragma: no cover
        raise RuntimeError(
            "`enable_proxy` == True, but `proxy` is not in `load_builtin_plugins`.\n"
            "Please add `proxy` to `load_builtin_plugins` in your settings file."
        )

    # Load other plugins from settings
    builtin_plugin_instances = load_builtin_plugins(*candidate_builtin_plugins) if candidate_builtin_plugins else set()
    plugin_instances = load_plugins(*plugins) if plugins else set()
    return builtin_plugin_instances | plugin_instances


async def register_proxy_func(func: Callable) -> None:
    full_func_name = f"{func.__module__}.{func.__name__}"
    if full_func_name not in _PROXY_REGISTRY:  # pragma: no cover
        raise RuntimeError(f"Function {full_func_name} is not registered as a proxy function.")

    api_reg = PluginApi(
        deployment_name=PROXY_PLUGIN_NAME,
        call_type=ApiType.PROXY,
        func_name="register_proxy_function",
    )
    await call_plugin_api(
        api_reg,
        None,
        func_name=full_func_name,
        func_callable=_PROXY_REGISTRY[full_func_name],
    )
