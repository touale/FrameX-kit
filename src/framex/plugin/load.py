from framex.plugin.model import Plugin

from . import _manager


def load_plugins(*plugin_dir: str) -> set[Plugin]:
    return _manager.load_all_plugin(plugin_dir)


def load_builtin_plugin(name: str) -> set[Plugin]:
    return load_plugins(f"framex.plugins.{name}")
