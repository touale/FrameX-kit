from . import _manager


def load_plugin(module_path: str):
    return _manager.load_plugin(module_path)
