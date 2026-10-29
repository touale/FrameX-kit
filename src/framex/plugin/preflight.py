"""Source-only admission checks for algorithm plugins, not a Python sandbox."""

from __future__ import annotations

import ast
import sys
from importlib.machinery import (
    BYTECODE_SUFFIXES,
    EXTENSION_SUFFIXES,
    SOURCE_SUFFIXES,
    ExtensionFileLoader,
    FileFinder,
    ModuleSpec,
    SourceFileLoader,
    SourcelessFileLoader,
)
from importlib.util import resolve_name
from pathlib import Path
from types import CodeType
from typing import NoReturn

_BUILTIN_ROOT = Path(__file__).resolve().parents[1] / "plugins"
_HOST_MODULES = ("framex.driver.ingress", "framex.driver.application")
_APP_TYPES = {"fastapi.FastAPI", "fastapi.applications.FastAPI", "starlette.applications.Starlette"}
_REQUEST_TYPES = {"fastapi.Request", "starlette.requests.Request"}
_APP_METHODS = {
    "add_middleware",
    "add_route",
    "add_api_route",
    "add_websocket_route",
    "add_api_websocket_route",
    "add_exception_handler",
    "add_event_handler",
    "include_router",
    "mount",
    "middleware",
    "exception_handler",
    "on_event",
    "route",
    "api_route",
    "websocket",
    "websocket_route",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
}
_MUTATING_METHODS = {
    "append",
    "extend",
    "insert",
    "remove",
    "pop",
    "clear",
    "update",
    "setdefault",
    "sort",
    "reverse",
    "__setitem__",
    "__delitem__",
    "__setattr__",
    "__delattr__",
}
_BUILTINS = {"eval", "exec", "compile", "__import__", "getattr", "setattr", "delattr"}
_HOST_CONTAINERS = (".router.routes", ".user_middleware", ".exception_handlers")


class PluginPreflightError(RuntimeError):
    """A plugin could not be admitted without executing its code."""


def find_source_spec(module_name: str) -> ModuleSpec | None:
    """Resolve filesystem modules without importing their parent packages."""
    search_path = list(sys.path)
    spec = None
    parts = module_name.split(".")
    for index in range(len(parts)):
        fullname = ".".join(parts[: index + 1])
        namespace_paths: list[str] = []
        spec = None
        for root in search_path:
            finder = FileFinder(
                str(Path(root or ".").resolve()),
                (ExtensionFileLoader, EXTENSION_SUFFIXES),
                (SourceFileLoader, SOURCE_SUFFIXES),
                (SourcelessFileLoader, BYTECODE_SUFFIXES),
            )
            candidate = finder.find_spec(fullname)
            if candidate is not None:
                if candidate.loader is not None:
                    spec = candidate
                    break
                namespace_paths.extend(candidate.submodule_search_locations or [])
        if spec is None and namespace_paths:
            spec = ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = namespace_paths
        if spec is None:
            return None
        if index < len(parts) - 1 and spec.submodule_search_locations is None:
            return None
        search_path = list(spec.submodule_search_locations or [])
    return spec


def is_builtin_source(module_name: str, filename: str) -> bool:
    return (module_name == "framex.plugins" or module_name.startswith("framex.plugins.")) and Path(
        filename
    ).resolve().is_relative_to(_BUILTIN_ROOT)


def source_module_name(path: Path) -> str:
    """Find an importable name for a discovered source outside the working directory too."""
    resolved = path.resolve()
    suffix = next((item for item in [*EXTENSION_SUFFIXES, ".pyc", ".py"] if resolved.name.endswith(item)), "")
    module_path = resolved.with_name(resolved.name.removesuffix(suffix)) if suffix else resolved
    for root in sorted(
        {Path(item or ".").resolve() for item in sys.path}, key=lambda item: len(item.parts), reverse=True
    ):
        if not resolved.is_relative_to(root):
            continue
        relative = module_path.relative_to(root)
        parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
        if parts and all(part.isidentifier() for part in parts):
            return ".".join(parts)
    raise PluginPreflightError(f"Cannot resolve plugin source: {path.name}")


def _is_host_reference(name: str) -> bool:
    return any(name == module or name.startswith(f"{module}.") for module in _HOST_MODULES)


class _SourceVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, module_name: str, is_package: bool) -> None:
        self.filename = filename
        self.package = module_name if is_package else module_name.rpartition(".")[0]
        self.bindings: dict[str, str] = {}
        self.imports: set[str] = set()

    def reject(self, node: ast.AST, reason: str) -> NoReturn:
        raise PluginPreflightError(f"{self.filename}:{getattr(node, 'lineno', 1)}: {reason}")

    @staticmethod
    def _annotation(node: ast.AST | None) -> ast.AST | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                return ast.increment_lineno(ast.parse(node.value, mode="eval").body, node.lineno - 1)
            except SyntaxError:
                return None
        return node

    def resolve(self, node: ast.AST | None) -> str:
        if isinstance(node, ast.Name):
            return self.bindings.get(node.id, f"builtins.{node.id}" if node.id in _BUILTINS else node.id)
        if isinstance(node, ast.Attribute):
            parent = self.resolve(node.value)
            if parent:
                if parent == "@request" and node.attr == "app":
                    return "@app"
                name = f"{parent}.{node.attr}"
                return self.bindings.get(name, name)
        if isinstance(node, ast.Subscript):
            if (
                self.resolve(node.value) == "@request.scope"
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == "app"
            ):
                return "@app"
            return self.resolve(node.value)
        if isinstance(node, ast.Call):
            name = self.resolve(node.func)
            if name in _APP_TYPES:
                return "@app"
            if name in _REQUEST_TYPES:
                return "@request"
            if name == "builtins.getattr" and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                parent = self.resolve(node.args[0])
                if parent and isinstance(node.args[1].value, str):
                    return (
                        "@app"
                        if parent == "@request" and node.args[1].value == "app"
                        else f"{parent}.{node.args[1].value}"
                    )
        return ""

    def _bind(self, target: ast.AST, value: str) -> None:
        if isinstance(target, ast.Name):
            self.bindings[target.id] = value
        elif isinstance(target, ast.Attribute) and (name := self.resolve(target)):
            self.bindings[name] = value

    def _check_write(self, target: ast.AST) -> None:
        if isinstance(target, ast.Tuple | ast.List):
            for item in target.elts:
                self._check_write(item)
        elif isinstance(target, ast.Attribute | ast.Subscript):
            name = self.resolve(target)
            if (
                name == "@app"
                or name.startswith("@app.")
                or name.endswith(_HOST_CONTAINERS)
                or _is_host_reference(name)
            ):
                attribute = target.attr if isinstance(target, ast.Attribute) else "container"
                self.reject(target, f"Modifying the host application {attribute} is forbidden")
            if isinstance(target, ast.Attribute) and target.attr in {
                "lifespan_context",
                "user_middleware",
                "middleware_stack",
                "exception_handlers",
            }:
                self.reject(target, f"Replacing application {target.attr} is forbidden")

    def _import(self, node: ast.AST, name: str) -> None:
        if _is_host_reference(name):
            self.reject(node, f"Access to {name} is forbidden")
        self.imports.add(name)

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            self._import(node, item.name)
            self.bindings[item.asname or item.name.split(".")[0]] = (
                item.name if item.asname else item.name.split(".")[0]
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        try:
            module = (
                resolve_name("." * node.level + (node.module or ""), self.package) if node.level else node.module or ""
            )
        except (ImportError, ValueError):
            self.reject(node, "Cannot resolve relative import")
        self._import(node, module)
        for item in node.names:
            if item.name == "*":
                self.reject(node, "Wildcard imports cannot be preflighted; import explicit names")
            name = f"{module}.{item.name}"
            self._import(node, name)
            self.bindings[item.asname or item.name] = name

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if _is_host_reference(name := self.resolve(node)):
            self.reject(node, f"Access to {name} is forbidden")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._check_write(target)
            self._bind(target, self.resolve(node.value))
            self.visit(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_write(node.target)
        parsed_annotation = self._annotation(node.annotation)
        if parsed_annotation is not None:
            self.visit(parsed_annotation)
        self.generic_visit(node)
        annotation = self.resolve(parsed_annotation)
        self._bind(
            node.target,
            "@app"
            if annotation in _APP_TYPES
            else "@request"
            if annotation in _REQUEST_TYPES
            else self.resolve(node.value),
        )

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_write(node.target)
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for target in node.targets:
            self._check_write(target)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.generic_visit(node)
        self._bind(node.target, self.resolve(node.value))

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for expression in [
            *node.decorator_list,
            *node.args.defaults,
            *[item for item in node.args.kw_defaults if item],
        ]:
            self.visit(expression)
        bindings = self.bindings
        self.bindings = bindings.copy()
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        arguments.extend(item for item in (node.args.vararg, node.args.kwarg) if item)
        for annotation in [node.returns, *[argument.annotation for argument in arguments]]:
            if parsed_annotation := self._annotation(annotation):
                self.visit(parsed_annotation)
        for argument in arguments:
            name = self.resolve(self._annotation(argument.annotation))
            self.bindings[argument.arg] = (
                "@app" if name in _APP_TYPES else "@request" if name in _REQUEST_TYPES else f"@local.{argument.arg}"
            )
        for statement in node.body:
            self.visit(statement)
        self.bindings = bindings
        self.bindings[node.name] = f"@local.{node.name}"

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_application = any(self.resolve(base) in _APP_TYPES for base in node.bases)
        for expression in [*node.bases, *node.decorator_list, *[item.value for item in node.keywords]]:
            self.visit(expression)
        bindings = self.bindings
        self.bindings = bindings.copy()
        for statement in node.body:
            self.visit(statement)
        self.bindings = bindings
        self.bindings[node.name] = "fastapi.FastAPI" if is_application else f"@local.{node.name}"

    def visit_Call(self, node: ast.Call) -> None:
        name = self.resolve(node.func)
        if name in _APP_TYPES:
            self.reject(node, "Creating a FastAPI/Starlette application in an algorithm plugin is forbidden")
        if name in {"builtins.eval", "builtins.exec", "builtins.compile"}:
            self.reject(node, "Dynamic code execution cannot be preflighted")
        if name in {"importlib.import_module", "builtins.__import__"}:
            if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                self.reject(node, "Dynamic import target cannot be resolved")
            target = node.args[0].value
            if target.startswith("."):
                self.reject(node, "Relative dynamic imports cannot be preflighted; use a regular import")
            self._import(node, target)
        if name in {"builtins.setattr", "builtins.delattr", "builtins.getattr"} and node.args:
            owner = self.resolve(node.args[0])
            if owner in {"@app", "framex"} or owner.startswith(("@app.", "framex.")):
                if name != "builtins.getattr":
                    self.reject(node, "Modifying the host application is forbidden")
                if (
                    len(node.args) < 2
                    or not isinstance(node.args[1], ast.Constant)
                    or not isinstance(node.args[1].value, str)
                ):
                    self.reject(node, "Dynamic framework attribute access cannot be preflighted")
                if _is_host_reference(f"{owner}.{node.args[1].value}"):
                    self.reject(node, "Access to the host application is forbidden")
        owner, _, method = name.rpartition(".")
        if (
            ((owner == "@app" or owner.startswith("@app.")) and method in _APP_METHODS | _MUTATING_METHODS)
            or (owner.endswith(_HOST_CONTAINERS) and method in _MUTATING_METHODS)
            or method
            in {
                "add_middleware",
                "add_exception_handler",
                "add_event_handler",
                "exception_handler",
                "middleware",
                "on_event",
            }
        ):
            self.reject(node, f"Modifying application via {method} is forbidden")
        self.generic_visit(node)


def inspect_plugin_sources(module_name: str, *, scan_package: bool = True) -> dict[str, CodeType]:
    """Check a plugin and snapshot its code before any package is imported."""
    entry = find_source_spec(module_name)
    if entry is None or (entry.origin is None and not entry.submodule_search_locations):
        raise PluginPreflightError(f"Cannot locate plugin source: {module_name}")
    if entry.origin and is_builtin_source(module_name, entry.origin):
        return {}
    entry_path = Path(entry.origin or next(iter(entry.submodule_search_locations or []))).resolve()
    top_spec = find_source_spec(module_name.split(".")[0])
    local_roots = [Path(item).resolve() for item in (top_spec.submodule_search_locations or [])] if top_spec else []
    standalone = not local_roots
    if standalone:
        local_roots = [entry_path.parent]
    codes: dict[str, CodeType] = {}
    visited: set[str] = set()
    pending = [module_name]
    if scan_package and entry.submodule_search_locations:
        for root in entry.submodule_search_locations:
            for path in sorted(Path(root).rglob("*.py")):
                relative = path.relative_to(root).with_suffix("")
                parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
                if "__pycache__" not in parts and all(part.isidentifier() for part in parts):
                    pending.append(".".join((module_name, *parts)))
            if any(path.is_symlink() and path.is_dir() for path in Path(root).rglob("*")):
                raise PluginPreflightError(f"Cannot preflight symlinked package directories: {module_name}")
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        spec = find_source_spec(name)
        if spec is None:
            continue  # An imported name can be an attribute rather than a module.
        parent = name.rpartition(".")[0]
        if parent and parent not in {"framex", "framex.plugins"}:
            pending.append(parent)
        if spec.origin is None and spec.submodule_search_locations:
            continue  # Namespace packages do not execute an initializer.
        if spec.origin is None or not isinstance(spec.loader, SourceFileLoader) or Path(spec.origin).suffix != ".py":
            raise PluginPreflightError(f"Source-only preflight required: {name}")
        if is_builtin_source(name, spec.origin):
            continue
        path = Path(spec.origin).resolve()
        label = next(
            (path.relative_to(root).as_posix() for root in local_roots if path.is_relative_to(root)), path.name
        )
        try:
            source = path.read_bytes()
            tree = ast.parse(source, filename=label)
            visitor = _SourceVisitor(label, name, bool(spec.submodule_search_locations))
            visitor.visit(tree)
            codes[name] = compile(tree, str(path), "exec", dont_inherit=True)
        except (OSError, SyntaxError, ValueError) as error:
            raise PluginPreflightError(
                f"{label}:{getattr(error, 'lineno', None) or 1}: Cannot read or compile plugin source"
            ) from error
        for imported in sorted(visitor.imports):
            imported_spec = find_source_spec(imported)
            if (
                imported_spec
                and imported_spec.origin
                and imported_spec.origin not in {"built-in", "frozen"}
                and any(
                    Path(imported_spec.origin).resolve().parent == root
                    if standalone
                    else Path(imported_spec.origin).resolve().is_relative_to(root)
                    for root in local_roots
                )
            ):
                pending.append(imported)
    return codes
