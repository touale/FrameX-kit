from framex.config import Settings
from framex.log import logger
from framex.plugin.model import Plugin

from . import _manager, get_loaded_plugins


def load_plugins(*plugin_dir: str) -> set[Plugin]:
    return _manager.load_plugins(plugin_dir)


def load_builtin_plugins(*names: str) -> set[Plugin]:
    return load_plugins(*[f"framex.plugins.{name}" for name in names])


@logger.catch(reraise=True)
def load_from_settings(settings: Settings) -> set[Plugin]:
    # Get all builtin_plugins
    loaded_builtin_plugins = {
        plugin.name for plugin in get_loaded_plugins() if plugin.module_name.startswith("framex.plugins.")
    }
    # Candidate builtin_plugins
    candidate_builtin_plugins = set(settings.load_builtin_plugins) - loaded_builtin_plugins
    # Check if proxy is enabled but not allow to load
    if (
        settings.server.enable_proxy
        and "proxy" not in loaded_builtin_plugins
        and "proxy" not in candidate_builtin_plugins
    ):  # pragma: no cover
        raise RuntimeError(
            "`enable_proxy` == True, but `proxy` is not in `load_builtin_plugins`.\n"
            "Please add `proxy` to `load_builtin_plugins` in your settings file."
        )

    # Load other plugins from settings
    builtin_plugin_instances = load_builtin_plugins(*candidate_builtin_plugins) if candidate_builtin_plugins else set()
    plugin_instances = load_plugins(*settings.load_plugins) if settings.load_plugins else set()
    return builtin_plugin_instances | plugin_instances
