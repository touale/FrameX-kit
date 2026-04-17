import html
import json
import re
import tomllib
from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml
from fastapi.responses import HTMLResponse

from framex.config import settings

SUPPORTED_EMBEDDED_CONFIG_SUFFIXES = (".yaml", ".yml", ".toml")

SENSITIVE_CONFIG_KEYWORDS = (
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "client_secret",
    "cookie",
    "session",
    "credential",
    "mysql",
)


def _normalize_whitelist_pattern(pattern: str) -> str:
    return pattern.strip().lstrip("/")


def _is_whitelisted_embedded_config_path(candidate: Path, workspace_root: Path, whitelist: Sequence[str]) -> bool:
    if not whitelist:
        return False

    relative_path = candidate.relative_to(workspace_root).as_posix()
    return any(
        fnmatch(relative_path, _normalize_whitelist_pattern(pattern)) for pattern in whitelist if pattern.strip()
    )


def _resolve_embedded_config_path(
    path_value: str,
    workspace_root: Path,
    whitelist: Sequence[str],
) -> Path | None:
    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():  # noqa
        candidate = (workspace_root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    if candidate.suffix.lower() not in SUPPORTED_EMBEDDED_CONFIG_SUFFIXES:
        return None
    if not candidate.is_file():
        return None

    try:
        candidate.relative_to(workspace_root)
    except ValueError:
        return None

    if not _is_whitelisted_embedded_config_path(candidate, workspace_root, whitelist):
        return None

    return candidate


def collect_embedded_config_files(
    config_data: Any,
    workspace_root: Path | None = None,
    whitelist: Sequence[str] = (),
) -> list[tuple[str, str]]:
    found_files: list[tuple[str, str]] = []
    visited_paths: set[Path] = set()
    resolved_workspace_root = (workspace_root or Path.cwd()).resolve()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for nested_value in value.values():
                walk(nested_value)
            return
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, str):
            return

        resolved_path = _resolve_embedded_config_path(value, resolved_workspace_root, whitelist)
        if resolved_path is None or resolved_path in visited_paths:
            return

        visited_paths.add(resolved_path)
        found_files.append((str(resolved_path), resolved_path.read_text(encoding="utf-8")))

    walk(config_data)
    return found_files


def _format_toml_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return json.dumps(key, ensure_ascii=False)


def _mask_sensitive_string(value: str) -> str:
    if not value:
        return value
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}{'*' * max(len(value) - 4, 4)}{value[-2:]}"


def _is_sensitive_config_key(key: str) -> bool:
    normalized_key = key.lower().replace("-", "_")
    return any(keyword in normalized_key for keyword in SENSITIVE_CONFIG_KEYWORDS)


def _should_mask_config_path(key_path: tuple[str, ...]) -> bool:
    if any(_is_sensitive_config_key(segment) for segment in key_path):
        return True
    if len(key_path) >= 2 and key_path[-2] == "rules" and "auth" in key_path:  # noqa
        return True
    return False


def mask_sensitive_config_data(config_data: Any, key_path: tuple[str, ...] = ()) -> Any:
    if isinstance(config_data, dict):
        return {
            key: mask_sensitive_config_data(value, key_path=(*key_path, str(key)))
            for key, value in config_data.items()
        }
    if isinstance(config_data, list):
        return [mask_sensitive_config_data(item, key_path=key_path) for item in config_data]
    if isinstance(config_data, str) and _should_mask_config_path(key_path):
        return _mask_sensitive_string(config_data)
    return config_data


def mask_sensitive_config_text(content: str) -> str:
    lines: list[str] = []
    pattern = re.compile(
        r"^(?P<prefix>\s*(?:-\s*)?[\"']?(?P<key>[A-Za-z0-9_.-]+)[\"']?\s*(?::|=)\s*)(?P<value>.*?)(?P<suffix>\s*(?:#.*)?)$"
    )

    for line in content.splitlines():
        match = pattern.match(line)
        if not match or not _is_sensitive_config_key(match.group("key")):
            lines.append(line)
            continue

        raw_value = match.group("value").strip()
        if not raw_value:
            lines.append(line)
            continue

        quote_char = ""
        if raw_value[0] in {'"', "'"} and raw_value[-1] == raw_value[0]:
            quote_char = raw_value[0]
            inner_value = raw_value[1:-1]
        else:
            inner_value = raw_value

        masked_value = _mask_sensitive_string(inner_value)
        rendered_value = f"{quote_char}{masked_value}{quote_char}" if quote_char else masked_value
        lines.append(f"{match.group('prefix')}{rendered_value}{match.group('suffix')}")

    return "\n".join(lines)


def _format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int | float):
        return str(value)
    if value is None:
        return '""'
    if isinstance(value, list):
        return f"[{', '.join(_format_toml_value(item) for item in value)}]"
    if isinstance(value, dict):
        items = ", ".join(f"{_format_toml_key(str(key))} = {_format_toml_value(item)}" for key, item in value.items())
        return f"{{ {items} }}"
    return json.dumps(value, ensure_ascii=False)


def _dump_toml_table(data: dict[str, Any], prefix: tuple[str, ...] = ()) -> list[str]:
    lines: list[str] = []
    nested_items: list[tuple[str, Any]] = []

    for key, value in data.items():
        if isinstance(value, dict):
            nested_items.append((key, value))
            continue
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            nested_items.append((key, value))
            continue
        lines.append(f"{_format_toml_key(str(key))} = {_format_toml_value(value)}")

    for key, value in nested_items:
        section_name = ".".join([*prefix, _format_toml_key(str(key))])
        if isinstance(value, dict):
            if lines:
                lines.append("")
            lines.append(f"[{section_name}]")
            lines.extend(_dump_toml_table(value, (*prefix, _format_toml_key(str(key)))))
            continue

        for item in value:
            if lines:
                lines.append("")
            lines.append(f"[[{section_name}]]")
            lines.extend(_dump_toml_table(item, (*prefix, _format_toml_key(str(key)))))

    return lines


def _format_plugin_config_toml(config_data: Any) -> str:
    if not isinstance(config_data, dict):
        return _format_toml_value(config_data)
    return "\n".join(_dump_toml_table(config_data))


def _normalize_display_config_paths(
    config_data: Any,
    workspace_root: Path | None = None,
    whitelist: Sequence[str] = (),
) -> Any:
    resolved_workspace_root = (workspace_root or Path.cwd()).resolve()
    if isinstance(config_data, dict):
        return {
            key: _normalize_display_config_paths(
                value,
                workspace_root=resolved_workspace_root,
                whitelist=whitelist,
            )
            for key, value in config_data.items()
        }
    if isinstance(config_data, list):
        return [
            _normalize_display_config_paths(
                item,
                workspace_root=resolved_workspace_root,
                whitelist=whitelist,
            )
            for item in config_data
        ]
    if isinstance(config_data, str):
        resolved_path = _resolve_embedded_config_path(
            config_data,
            resolved_workspace_root,
            whitelist,
        )
        if resolved_path is not None:
            return _to_display_embedded_config_path(str(resolved_path), workspace_root=resolved_workspace_root)

        candidate = Path(config_data).expanduser()
        try:
            if not candidate.is_absolute():
                candidate = (resolved_workspace_root / candidate).resolve()
            else:
                candidate = candidate.resolve()
        except OSError:
            return config_data

        if candidate.suffix.lower() in SUPPORTED_EMBEDDED_CONFIG_SUFFIXES and candidate.is_file():
            return "[restricted config path]"
    return config_data


def mask_sensitive_embedded_config_content(file_path: str, content: str) -> str:
    suffix = Path(file_path).suffix.lower()

    try:
        if suffix == ".toml":
            parsed = tomllib.loads(content)
            return _format_plugin_config_toml(mask_sensitive_config_data(parsed))
        if suffix in {".yaml", ".yml"}:
            parsed = yaml.safe_load(content)
            masked = mask_sensitive_config_data(parsed)
            return yaml.safe_dump(masked, allow_unicode=True, sort_keys=False).rstrip()
    except Exception:
        return mask_sensitive_config_text(content)

    return mask_sensitive_config_text(content)


def _to_display_embedded_config_path(file_path: str, workspace_root: Path | None = None) -> str:
    resolved_workspace_root = (workspace_root or Path.cwd()).resolve()
    resolved_file_path = Path(file_path).resolve()
    try:
        return resolved_file_path.relative_to(resolved_workspace_root).as_posix()
    except ValueError:
        return resolved_file_path.as_posix()


def build_plugin_config_html(config_data: Any, embedded_files: list[tuple[str, str]] | None = None) -> HTMLResponse:
    workspace_root = Path.cwd().resolve()
    embedded_path_whitelist = tuple(settings.docs.embedded_config_file_whitelist or [])
    normalized_config_data = _normalize_display_config_paths(
        config_data,
        workspace_root=workspace_root,
        whitelist=embedded_path_whitelist,
    )
    masked_config_data = mask_sensitive_config_data(normalized_config_data)
    escaped_toml: str = html.escape(_format_plugin_config_toml(masked_config_data))
    masked_embedded_files = [
        (
            _to_display_embedded_config_path(file_path),
            mask_sensitive_embedded_config_content(file_path, file_content),
        )
        for file_path, file_content in (embedded_files or [])
    ]
    embedded_sections = "".join(
        f"""
    <section class=\"config-shell config-shell--embedded\">\n        <header class=\"config-header\">\n            <h2 class=\"config-title\">Referenced Config: {html.escape(file_path)}</h2>\n        </header>\n        <pre class=\"config-body\">{html.escape(file_content)}</pre>\n    </section>
        """
        for file_path, file_content in masked_embedded_files
    )
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Plugin Config</title>
    <style>
        body {{
            margin: 0;
            padding: 24px;
            background: #f8fafc;
            color: #0f172a;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}

        .config-shell {{
            max-width: 960px;
            margin: 0 auto 16px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
        }}

        .config-header {{
            padding: 16px 20px;
            border-bottom: 1px solid #e2e8f0;
            background: #ffffff;
        }}

        .config-title {{
            margin: 0;
            font-size: 15px;
            font-weight: 700;
        }}

        .config-body {{
            margin: 0;
            padding: 20px;
            background: #ffffff;
            color: #0f172a;
            font-size: 13px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-break: break-word;
            overflow: auto;
        }}
    </style>
</head>
<body>
    <section class=\"config-shell\">
        <header class=\"config-header\">
            <h1 class=\"config-title\">Plugin Config (TOML)</h1>
        </header>
        <pre class=\"config-body\">{escaped_toml}</pre>
    </section>
    {embedded_sections}
</body>
</html>
        """
    )
