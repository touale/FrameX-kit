import importlib
import importlib.util
import py_compile
import sys
import textwrap
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path

import pytest

import framex
import framex.plugin as plugin_module
import framex.plugin.load as load_module
import framex.plugin.manage as manage_module
from framex.plugin.manage import PluginManager
from framex.plugin.preflight import inspect_plugin_sources
from framex.utils.docs import build_swagger_ui_html

_METADATA = """
from framex.plugin import PluginMetadata
__plugin_meta__ = PluginMetadata(
    name="sample", version="1.0", description="Sample algorithm", author="test",
    url="https://example.test/plugin",
)
"""


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")


@pytest.fixture
def plugin_tree(tmp_path, monkeypatch):
    package = tmp_path / "preflight_sample"
    _write(package / "__init__.py", "")
    monkeypatch.syspath_prepend(str(tmp_path))
    manager = PluginManager(silent=True)
    monkeypatch.setattr(manage_module, "_manager", manager)
    monkeypatch.setattr(plugin_module, "_manager", manager)
    monkeypatch.setattr(load_module, "_manager", manager)
    yield package, manager
    for name in list(sys.modules):
        if name == "preflight_sample" or name.startswith("preflight_sample."):
            del sys.modules[name]


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        ("from framex.driver.ingress import app", "framex.driver.ingress"),
        ("from framex.driver import application as host", "framex.driver.application"),
        ("import framex as fx\nhost = fx.driver.ingress.app", "framex.driver.ingress"),
        ("from fastapi import FastAPI as WebApp\napplication = WebApp()", "Creating a FastAPI"),
        ("from starlette.applications import Starlette as WebApp\napplication = WebApp()", "Creating a FastAPI"),
        (
            """
            from fastapi import FastAPI
            def install(application: FastAPI):
                router = application.router
                router.lifespan_context = lambda app: None
            """,
            "host application",
        ),
        ("def install(application):\n    application.user_middleware = []", "user_middleware"),
        (
            """
            from fastapi import FastAPI
            def install(application: FastAPI):
                application.router.routes[:] = []
            """,
            "host application",
        ),
        (
            """
            from fastapi import FastAPI
            def install(application: FastAPI):
                routes = application.router.routes
                routes.clear()
            """,
            "via clear",
        ),
        (
            """
            from fastapi import FastAPI
            def install(application: FastAPI):
                @application.exception_handler(Exception)
                def error_handler(request, exc):
                    pass
            """,
            "exception_handler",
        ),
        (
            """
            from fastapi import FastAPI as App
            def install(application: "App"):
                register = application.add_middleware
                register(object)
            """,
            "add_middleware",
        ),
        (
            """
            from fastapi import FastAPI
            class Installer:
                def __init__(self, application: FastAPI):
                    self.host = application
                    self.host.mount('/assets', object())
            """,
            "via mount",
        ),
        (
            """
            from fastapi import Request
            async def handler(request: Request):
                request.app.state.deployments_dict.clear()
            """,
            "via clear",
        ),
        (
            """
            from starlette.requests import Request as HttpRequest
            def handler(request: HttpRequest):
                host = request.scope['app']
                host.add_middleware(object)
            """,
            "add_middleware",
        ),
        (
            """
            from fastapi import Request
            def handler(request: Request):
                setattr(request.app.router, 'lifespan_context', None)
            """,
            "host application",
        ),
        ("from builtins import exec as execute\nexecute('pass')", "Dynamic code"),
        ("def handler(value: exec('pass')):\n    pass", "Dynamic code"),
        ("def handler() -> eval('str'):\n    pass", "Dynamic code"),
        ("def handler(value: \"__import__('framex.driver.ingress')\"):\n    pass", "framex.driver.ingress"),
        ("import builtins\nrun = builtins.compile\nrun('pass', '<plugin>', 'exec')", "Dynamic code"),
        ("import importlib as loader\nloader.import_module(plugin_name)", "Dynamic import target"),
        ("__import__('framex.driver.ingress')", "framex.driver.ingress"),
        ("from fastapi import *", "Wildcard imports"),
        (
            """
            from fastapi import FastAPI
            class WebApp(FastAPI):
                pass
            application = WebApp()
            """,
            "Creating a FastAPI",
        ),
        (
            """
            import framex
            def indirect(name):
                return getattr(framex, name)
            """,
            "Dynamic framework attribute",
        ),
    ],
)
def test_preflight_rejects_before_any_plugin_code_executes(plugin_tree, source, reason):
    package, manager = plugin_tree
    marker = package / "executed"
    _write(
        package / "__init__.py",
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + textwrap.dedent(source),
    )

    assert framex.load_plugins("preflight_sample") == set()
    assert not marker.exists()
    assert "preflight_sample" not in sys.modules
    assert manager._plugins == {}
    assert manager.http_plugin_apis == []
    assert manager.func_plugin_apis == []
    error = manager._plugin_load_errors["preflight_sample"]
    assert "__init__.py:" in error
    assert reason in error
    assert str(package.parent) not in error


def test_preflight_checks_unimported_submodules_and_does_not_retry(plugin_tree):
    package, manager = plugin_tree
    _write(package / "__init__.py", _METADATA)
    _write(package / "service" / "__init__.py", "")
    violation = package / "service" / "application.py"
    _write(violation, "from fastapi import FastAPI\napp = FastAPI()")

    assert framex.load_plugins("preflight_sample") == set()
    error = manager._plugin_load_errors["preflight_sample"]
    assert "service/application.py:2" in error
    _write(violation, "")
    assert framex.load_plugins("preflight_sample") == set()
    assert manager._plugin_load_errors["preflight_sample"] == error


@pytest.mark.parametrize("selector", ["preflight_sample.plugins", "directory"])
def test_directory_discovery_keeps_valid_siblings(plugin_tree, selector):
    package, manager = plugin_tree
    directory = package / "plugins"
    _write(directory / "__init__.py", "")
    _write(directory / "good.py", _METADATA)
    _write(directory / "bad.py", "from framex.driver.ingress import app")

    plugins = framex.load_plugins(str(directory) if selector == "directory" else selector)

    assert {plugin.name for plugin in plugins} == {"good"}
    assert "bad" in manager._plugin_load_errors
    assert "preflight_sample.plugins.bad" not in sys.modules


@pytest.mark.parametrize("selector", ["preflight_sample.plugins", "preflight_sample.plugins.good", "directory"])
def test_parent_package_is_checked_before_discovery_or_import(plugin_tree, selector):
    package, manager = plugin_tree
    marker = package / "parent_executed"
    _write(
        package / "__init__.py",
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\nfrom framex.driver.ingress import app",
    )
    directory = package / "plugins"
    _write(directory / "__init__.py", "")
    _write(directory / "good.py", _METADATA)

    assert framex.load_plugins(str(directory) if selector == "directory" else selector) == set()
    assert not marker.exists()
    assert "preflight_sample" not in sys.modules
    assert manager._plugins == {}


@pytest.mark.parametrize("unsafe_parent", [False, True])
def test_namespace_discovery_checks_source_parents(plugin_tree, unsafe_parent):
    package, manager = plugin_tree
    if unsafe_parent:
        _write(package / "__init__.py", "from framex.driver.ingress import app")
    _write(package / "plugins" / "good.py", _METADATA)

    plugins = framex.load_plugins("preflight_sample.plugins")

    assert {plugin.name for plugin in plugins} == (set() if unsafe_parent else {"good"})
    if unsafe_parent:
        assert "plugins" in manager._plugin_load_errors
        assert "preflight_sample" not in sys.modules


def test_single_file_checks_local_imports_outside_its_package(plugin_tree):
    package, manager = plugin_tree
    _write(package / "helpers.py", "from framex.driver.application import create_fastapi_application")
    _write(package / "plugins" / "__init__.py", "")
    _write(package / "plugins" / "algorithm.py", _METADATA + "\nfrom preflight_sample import helpers")

    assert framex.load_plugins("preflight_sample.plugins.algorithm") == set()
    assert "helpers.py:1" in manager._plugin_load_errors["algorithm"]
    assert "preflight_sample" not in sys.modules


def test_dependency_cannot_import_another_configured_plugin_without_full_preflight(plugin_tree):
    package, manager = plugin_tree
    directory = package / "plugins"
    marker = package / "dependency_executed"
    _write(directory / "__init__.py", "")
    _write(directory / "consumer.py", _METADATA + "\nfrom . import dependency")
    _write(
        directory / "dependency" / "__init__.py",
        _METADATA + f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()",
    )
    _write(directory / "dependency" / "application.py", "from fastapi import FastAPI\napp = FastAPI()")

    assert framex.load_plugins(str(directory)) == set()
    assert manager._plugins == {}
    assert not marker.exists()
    assert "consumer" in manager._plugin_load_errors
    assert "dependency" in manager._plugin_load_errors


def test_single_file_follows_literal_dynamic_local_imports(plugin_tree):
    package, manager = plugin_tree
    _write(package / "helpers.py", "from fastapi import FastAPI\napp = FastAPI()")
    _write(
        package / "algorithm.py",
        _METADATA + "\nfrom importlib import import_module as load\nload('preflight_sample.helpers')",
    )
    assert framex.load_plugins("preflight_sample.algorithm") == set()
    assert "helpers.py:2" in manager._plugin_load_errors["algorithm"]


def test_unreadable_source_is_rejected_without_importing(plugin_tree, monkeypatch):
    package, manager = plugin_tree
    source = package / "__init__.py"
    _write(source, _METADATA)
    original_read = Path.read_bytes

    def read_bytes(path):
        if path == source:
            raise PermissionError("test")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    assert framex.load_plugins("preflight_sample") == set()
    assert "Cannot read or compile" in manager._plugin_load_errors["preflight_sample"]
    assert "preflight_sample" not in sys.modules


def test_preflight_preserves_normal_algorithm_apis_and_request_types(plugin_tree):
    package, manager = plugin_tree
    _write(package / "application.py", "def calculate(value: int) -> int:\n    return value + 1")
    _write(
        package / "__init__.py",
        _METADATA
        + """
from fastapi import Request, Response, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from framex.driver.cache import CacheContext
from framex.plugin import BasePlugin, on_register, on_request

class Input(BaseModel):
    application: str

def build_key(request: Request, context: CacheContext):
    return request.url.path

@on_register()
class Algorithm(BasePlugin):
    @on_request('/preflight/echo', methods=['POST'], raw_response=True)
    async def echo(self, model: Input):
        # application.router.lifespan_context = malicious
        return JSONResponse({'message': 'app.add_middleware()'})
""",
    )

    plugins = framex.load_plugins("preflight_sample")

    assert {plugin.name for plugin in plugins} == {"preflight_sample"}
    assert len(manager.http_plugin_apis) == 1
    assert manager.http_plugin_apis[0].raw_response is True
    assert manager._plugin_load_errors == {}


@pytest.mark.parametrize("source", ["def broken(:", "# coding: missing_encoding\nx = 1"])
def test_unparseable_source_is_rejected_with_location(plugin_tree, source):
    package, manager = plugin_tree
    _write(package / "__init__.py", source)
    assert framex.load_plugins("preflight_sample") == set()
    assert "Cannot read or compile" in manager._plugin_load_errors["preflight_sample"]


def test_plugin_entry_without_source_is_rejected(plugin_tree):
    package, manager = plugin_tree
    source = package / "algorithm.py"
    _write(source, _METADATA)
    py_compile.compile(str(source), cfile=str(source.with_suffix(".pyc")), doraise=True)
    source.unlink()

    assert framex.load_plugins("preflight_sample.algorithm") == set()
    assert "Source-only preflight required" in manager._plugin_load_errors["algorithm"]


def test_directory_discovery_rejects_native_entry_without_loading_it(plugin_tree):
    package, manager = plugin_tree
    _write(package / "plugins" / "__init__.py", "")
    _write(package / "plugins" / f"native{EXTENSION_SUFFIXES[0]}", "")
    _write(package / "plugins" / "good.py", _METADATA)

    assert {plugin.name for plugin in framex.load_plugins(str(package / "plugins"))} == {"good"}
    assert "Source-only preflight required" in manager._plugin_load_errors["native"]
    assert "preflight_sample.plugins.native" not in sys.modules


def test_admitted_source_is_executed_instead_of_cached_bytecode(plugin_tree):
    package, _ = plugin_tree
    source = package / "__init__.py"
    marker = package / "bytecode_executed"
    _write(source, f"from pathlib import Path\nPath({str(marker)!r}).touch()")
    py_compile.compile(str(source), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    _write(source, _METADATA)

    assert len(framex.load_plugins("preflight_sample")) == 1
    assert not marker.exists()


def test_preflight_failure_is_rendered_in_existing_docs_status(plugin_tree):
    package, _ = plugin_tree
    _write(package / "__init__.py", "from framex.driver.ingress import app")
    framex.load_plugins("preflight_sample")

    response = build_swagger_ui_html(
        openapi_url="/openapi.json", title="Test docs", plugin_infos=framex.plugin.get_runtime_plugin_infos()
    )
    html = bytes(response.body).decode()
    assert "preflight_sample" in html
    assert "PluginPreflightError" in html
    assert "__init__.py:1" in html


def test_builtin_trust_uses_source_location_not_module_prefix(plugin_tree):
    package, _ = plugin_tree
    from framex.plugin.preflight import is_builtin_source

    assert inspect_plugin_sources("framex.plugins.proxy") == {}
    assert not is_builtin_source("framex.plugins.proxy", str(package / "__init__.py"))


@pytest.mark.parametrize("use_ray", [False, True])
def test_run_rejects_illegal_plugin_before_initializing_deployments(plugin_tree, monkeypatch, use_ray):
    package, manager = plugin_tree
    _write(package / "__init__.py", "from framex.driver.ingress import app")

    class StopBeforeServingError(Exception):
        pass

    def check_deployments(**kwargs):
        assert manager._plugins == {}
        assert "preflight_sample" in manager._plugin_load_errors
        raise StopBeforeServingError

    monkeypatch.setattr(plugin_module, "init_all_deployments", check_deployments)
    with pytest.raises(StopBeforeServingError):
        framex.run(use_ray=use_ray, load_plugins=["preflight_sample"], load_builtin_plugins=[], enable_proxy=False)
    assert "preflight_sample" not in sys.modules


def test_source_snapshot_includes_parents_and_deferred_submodules(plugin_tree):
    package, _ = plugin_tree
    _write(package / "__init__.py", "version = 'checked'")
    _write(package / "algorithm" / "__init__.py", _METADATA)
    _write(package / "algorithm" / "helper.py", "version = 'checked'")
    codes = inspect_plugin_sources("preflight_sample.algorithm")
    manage_module._manager._checked_sources.update(codes)
    _write(package / "__init__.py", "raise RuntimeError('unchecked parent')")
    _write(package / "algorithm" / "helper.py", "raise RuntimeError('unchecked helper')")

    parent = importlib.import_module("preflight_sample")
    helper = importlib.import_module("preflight_sample.algorithm.helper")
    assert parent.version == "checked"
    assert helper.version == "checked"
