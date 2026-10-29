# Portions of this file are derived from NoneBot2:
# https://github.com/nonebot/nonebot2/blob/82cdaccd188c986a4c5e9600c53d5705a8735259/nonebot/plugin/manager.py
# Copyright (c) 2020 NoneBot Team
# Licensed under the MIT License (see full license at the URL above).
from __future__ import annotations

import importlib
import pkgutil
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder, SourceFileLoader
from itertools import chain
from pathlib import Path
from types import CodeType, ModuleType

from framex.config import settings
from framex.log import logger
from framex.plugin.model import ApiType, Plugin, PluginApi, PluginMetadata
from framex.plugin.preflight import PluginPreflightError, find_source_spec, inspect_plugin_sources, source_module_name
from framex.utils import escape_tag, shorten_str

_PLUGIN_LOAD_ERROR_MAX_LENGTH = 300


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit(".", 1)[-1]


def _summarize_plugin_load_error(error: Exception) -> str:
    reason = " ".join(str(error).split())
    summary = type(error).__name__
    if reason:
        summary = f"{summary}: {reason}"
    return shorten_str(summary, _PLUGIN_LOAD_ERROR_MAX_LENGTH)


class PluginManager:
    def __init__(self, silent: bool = False) -> None:
        self.silent = silent

        self._third_party_plugin_ids: dict[str, str] = {}
        self._searched_plugin_ids: dict[str, str] = {}
        self._install_plugin_ids: list[str] = []

        self._plugins: dict[str, Plugin] = {}
        self._plugin_apis: dict[ApiType, dict[str, PluginApi]] = defaultdict(dict)
        self._plugin_load_errors: dict[str, str] = {}
        self._checked_sources: dict[str, CodeType] = {}
        self._preflighted_plugins: set[str] = set()

    @property
    def all_plugin_apis(self) -> dict[ApiType, dict[str, PluginApi]]:
        if not self._plugin_apis:
            for plugin in self._plugins.values():
                for dep in plugin.deployments:
                    http_api_names = []
                    func_api_names = []
                    for api in dep.plugin_apis:
                        api_name = f"{api.deployment_name}.{api.func_name}"
                        is_func = api.call_type in {ApiType.FUNC, ApiType.ALL}
                        is_http = api.call_type in {ApiType.HTTP, ApiType.ALL}
                        if is_func:
                            self._plugin_apis[ApiType.FUNC][api_name] = api
                            func_api_names.append(api_name)

                        if api.api and is_http:
                            self._plugin_apis[ApiType.HTTP][api.api] = api
                            http_api_names.append(api.api)

                    if not dep.plugin_apis:
                        logger.opt(colors=True).warning(f"<r>No relevant API found in plugin({plugin.name})</r>")
                        continue

                    if http_api_names:
                        logger.opt(colors=True).success(
                            f'Found plugin HTTP API "<g>{http_api_names}</g>" from plugin({plugin.name})'
                        )
                    if func_api_names:
                        logger.opt(colors=True).success(
                            f'Found plugin FUNC API "<g>{func_api_names}</g>" from plugin({plugin.name})'
                        )
        return self._plugin_apis

    @property
    def http_plugin_apis(self) -> list[PluginApi]:
        return list(self.all_plugin_apis[ApiType.HTTP].values())

    @property
    def func_plugin_apis(self) -> list[PluginApi]:
        return list(self.all_plugin_apis[ApiType.FUNC].values())

    @property
    def controlled_modules(self) -> dict[str, str]:
        return dict(chain(self._third_party_plugin_ids.items(), self._searched_plugin_ids.items()))

    @property
    def third_party_plugins(self) -> set[str]:
        return set(self._third_party_plugin_ids.keys())

    @property
    def searched_plugins(self) -> set[str]:
        return set(self._searched_plugin_ids.keys())

    @property
    def available_plugins(self) -> set[str]:
        return self.third_party_plugins | self.searched_plugins

    @logger.catch
    def _prepare_plugins(self, plugins_path: set[str]) -> None:
        self._plugin_apis = defaultdict(dict)
        searched_plugins = set()
        third_party_plugins = set()

        for plugin_path in plugins_path:
            if "/" in plugin_path:
                searched_plugins.add(plugin_path)
            else:
                if (
                    plugin_path.endswith(".plugins")
                    and (spec := find_source_spec(plugin_path))
                    and spec.submodule_search_locations
                ):
                    try:
                        self._checked_sources.update(inspect_plugin_sources(plugin_path, scan_package=False))
                    except Exception as error:
                        self._record_load_error(_module_name_to_plugin_name(plugin_path), error)
                        continue
                    searched_plugins.update(spec.submodule_search_locations)
                else:
                    third_party_plugins.add(plugin_path)

        # check third party plugins
        for plugin in third_party_plugins:
            plugin_id = _module_name_to_plugin_name(plugin)
            if plugin_id in self._third_party_plugin_ids:
                if self._third_party_plugin_ids[plugin_id] == plugin:
                    continue
                raise RuntimeError(f"Plugin already exists: {plugin_id}. Check for duplicate plugin names.")

            self._third_party_plugin_ids[plugin_id] = plugin

        # check plugins in search path
        for module_info in pkgutil.iter_modules(searched_plugins):
            # ignore if startswith "_"
            if module_info.name.startswith("_"):
                continue
            if not (module_spec := module_info.module_finder.find_spec(module_info.name, None)):
                continue
            if not module_spec.origin:
                continue
            # get module name from path, pkgutil does not return the actual module name
            module_path = Path(module_spec.origin).resolve()
            module_name = source_module_name(module_path)
            plugin_id = module_name.rsplit(".", 1)[-1]
            if plugin_id in self._third_party_plugin_ids or plugin_id in self._searched_plugin_ids:
                if self.controlled_modules[plugin_id] == module_name:
                    continue
                raise RuntimeError(f"Plugin already exists: {plugin_id}! Check your plugin name")
            self._searched_plugin_ids[plugin_id] = module_name

    def load_plugins(self, plugins_path: Iterable[str]) -> set[Plugin]:
        plugins_path = set(plugins_path or [])
        self._prepare_plugins(plugins_path)
        return set(filter(None, (self._load_plugin(name) for name in self.available_plugins)))

    def _load_plugin(self, name: str) -> Plugin | None:
        if name in self._install_plugin_ids:
            return None
        self._install_plugin_ids.append(name)

        try:
            # load using plugin id
            if name in self._third_party_plugin_ids:
                module_name = self._third_party_plugin_ids[name]
            elif name in self._searched_plugin_ids:
                module_name = self._searched_plugin_ids[name]
            # load using module name
            elif name in self._third_party_plugin_ids.values() or name in self._searched_plugin_ids.values():
                module_name = name
            else:
                raise RuntimeError(f"Plugin not found: {name}! Check your plugin name")
            self._preflight_plugin(module_name)
            module = importlib.import_module(module_name)
            if (plugin := getattr(module, "__plugin__", None)) is None or not isinstance(plugin, Plugin):
                raise RuntimeError(
                    f"Module {module.__name__} is not loaded as a plugin! Make sure not to import it before loading."
                )
            logger.opt(colors=True).success(
                f'Succeeded to load plugin "<g>{escape_tag(plugin.name)}</g>" from {plugin.module_name}'
            )
            self._plugin_load_errors.pop(name, None)
            return plugin  # type: ignore
        except Exception as e:
            self._record_load_error(name, e)
            return None

    def _record_load_error(self, name: str, error: Exception) -> None:
        self._plugin_load_errors[name] = _summarize_plugin_load_error(error)
        logger.opt(colors=True, exception=error if not self.silent else False).error(
            f'<r><bg #f8bbd0>Failed to import "{escape_tag(name)}"</bg #f8bbd0></r>, reason: {escape_tag(str(error))}'
        )

    def _preflight_plugin(self, module_name: str) -> None:
        plugin_id = _module_name_to_plugin_name(module_name)
        if plugin_id in self._plugin_load_errors:
            raise PluginPreflightError(f"Plugin disabled for this run: {plugin_id}")
        if module_name not in self._preflighted_plugins:
            self._checked_sources.update(inspect_plugin_sources(module_name))
            self._preflighted_plugins.add(module_name)

    def new_plugin(
        self,
        module_name: str,
        module: ModuleType,
    ) -> Plugin:
        plugin_id = _module_name_to_plugin_name(module_name)
        if plugin_id in self._plugins:
            raise RuntimeError(f"Plugin {plugin_id} already exists! Check your plugin name.")
        plugin = Plugin(
            name=plugin_id,
            module=module,
            module_name=module_name,
        )
        self._plugins[plugin_id] = plugin
        return plugin

    def revert_plugin(self, plugin: Plugin) -> None:
        if plugin.name not in self._plugins:
            raise RuntimeError("Plugin not found!")
        del self._plugins[plugin.name]

    def get_api(self, api_name: str) -> PluginApi | None:
        if api_name.startswith("/"):
            api = self.all_plugin_apis[ApiType.HTTP].get(api_name)
        else:
            api = self.all_plugin_apis[ApiType.FUNC].get(api_name)
        return api


class PluginFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        from . import _manager

        if _manager:
            if code := _manager._checked_sources.get(fullname):
                loader_type = PluginLoader if fullname in _manager.controlled_modules.values() else CheckedSourceLoader
                return importlib.util.spec_from_file_location(
                    fullname, code.co_filename, loader=loader_type(fullname, code.co_filename)
                )
            module_spec = PathFinder.find_spec(fullname, path, target)
            if not module_spec:
                return None
            module_origin = module_spec.origin
            if not module_origin:
                return None
            if fullname in _manager.controlled_modules.values():
                module_spec.loader = PluginLoader(fullname, module_origin)
                return module_spec
        return None


class CheckedSourceLoader(SourceFileLoader):
    def get_code(self, fullname: str) -> CodeType | None:
        from . import _manager

        if code := _manager._checked_sources.get(fullname):
            return code
        return super().get_code(fullname)


class PluginLoader(CheckedSourceLoader):
    def __init__(self, fullname: str, path: str) -> None:
        self.loaded = False
        super().__init__(fullname, path)

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        if self.name in sys.modules:
            self.loaded = True
            return sys.modules[self.name]
        return super().create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        if self.loaded:
            return

        from . import _manager

        try:
            _manager._preflight_plugin(self.name)
        except Exception as error:
            _manager._record_load_error(_module_name_to_plugin_name(self.name), error)
            raise

        # create plugin before executing
        plugin = _manager.new_plugin(
            self.name,
            module,
        )
        setattr(module, "__plugin__", plugin)

        # enter plugin context
        from . import _current_plugin

        _plugin_token = _current_plugin.set(plugin)

        try:
            super().exec_module(module)
        except Exception:
            _manager.revert_plugin(plugin)
            raise
        finally:
            # leave plugin context
            _current_plugin.reset(_plugin_token)

        # get plugin metadata
        metadata: PluginMetadata | None = getattr(module, "__plugin_meta__", None)
        plugin.metadata = metadata
        # Mkdir data dir for plugin


# Insert a custom plugin module finder into the front of the Python import system to intercept and load plugin modules
sys.meta_path.insert(0, PluginFinder())

_manager: PluginManager = PluginManager(silent=settings.test.silent)
