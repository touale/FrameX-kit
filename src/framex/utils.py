import base64
import importlib
import inspect
import json
import re
import zlib
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from itertools import cycle
from pathlib import Path
from typing import Any

from fastapi.responses import HTMLResponse
from pydantic import BaseModel


def plugin_to_deployment_name(plugin_name: str, obj_name: str) -> str:
    return f"{plugin_name}.{obj_name}"


def path_to_module_name(path: Path) -> str:
    """Convert path to module name"""
    rel_path = path.resolve().relative_to(Path.cwd().resolve())
    if rel_path.stem == "__init__":
        module_name = ".".join(rel_path.parts[:-1])
    else:
        module_name = ".".join([*rel_path.parts[:-1], rel_path.stem])  # type: ignore
    return module_name.removeprefix("src.")


def escape_tag(s: str) -> str:
    """Used to escape `<tag>` type special tags when recording color logs"""
    return re.sub(r"</?((?:[fb]g\s)?[^<>\s]*)>", r"\\\g<0>", s)


def extract_method_params(func: Callable) -> list[tuple[str, Any]]:
    sig = inspect.signature(func)
    params = []
    for param in sig.parameters.values():
        if param.name == "self":
            continue
        params.append((param.name, param.annotation))
    return params


class StreamEnventType(StrEnum):
    MESSAGE_CHUNK = "message_chunk"
    FINISH = "finish"
    ERROR = "error"
    DEBUG = "debug"


def make_stream_event(event_type: StreamEnventType | str, data: str | dict[str, Any] | BaseModel | None = None) -> str:
    if not data:
        data = {}
    elif isinstance(data, BaseModel):
        data = data.model_dump()
    elif isinstance(data, str):
        data = {"content": data}
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def xor_crypt(data: bytes, key: str = "01234567890abcdefghijklmnopqrstuvwxyz") -> bytes:
    return bytes(a ^ b for a, b in zip(data, cycle(key.encode())))


def cache_encode(data: Any) -> str:
    def transform(obj: Any) -> Any:
        if hasattr(obj, "__dict__"):
            raw_attributes = {k: transform(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
            return {
                "__type__": "dynamic_obj",
                "__module__": obj.__class__.__module__,
                "__class__": obj.__class__.__name__,
                "data": raw_attributes,
            }
        if isinstance(obj, list):
            return [transform(i) for i in obj]
        if isinstance(obj, dict):
            return {k: transform(v) for k, v in obj.items()}
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return obj

    json_str = json.dumps(transform(data), ensure_ascii=False)
    compressed = zlib.compress(json_str.encode("utf-8"))
    encrypted = xor_crypt(compressed)
    return base64.b64encode(encrypted).decode("ascii")


def cache_decode(res: Any) -> Any:
    current = res
    while isinstance(current, str):
        try:
            decoded_bytes = base64.b64decode(current, validate=True)
            current = zlib.decompress(xor_crypt(decoded_bytes)).decode("utf-8")
        except Exception:
            try:
                temp = json.loads(current)
                if temp == current:
                    break
                current = temp
            except Exception:
                break

    def restore_models(item: Any) -> Any:
        if isinstance(item, list):
            return [restore_models(i) for i in item]

        if isinstance(item, dict):
            if item.get("__type__") == "dynamic_obj":
                try:
                    module = importlib.import_module(item["__module__"])
                    cls = getattr(module, item["__class__"])

                    cleaned_data = {k: restore_models(v) for k, v in item["data"].items()}

                    if hasattr(cls, "model_validate"):
                        return cls.model_validate(cleaned_data)
                    return cls(**cleaned_data)
                except Exception:
                    from types import SimpleNamespace

                    return SimpleNamespace(**{k: restore_models(v) for k, v in item["data"].items()})

            return {k: restore_models(v) for k, v in item.items()}

        return item

    return restore_models(current)


def format_uptime(delta: timedelta) -> str:
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def safe_error_message(e: Exception) -> str:
    if hasattr(e, "cause") and e.cause:
        return str(e.cause)
    if e.args:
        return str(e.args[0])
    return "Internal Server Error"


def shorten_str(data: str, max_len: int = 45) -> str:
    return data if len(data) <= max_len else data[: max_len - 3] + "..."


def build_swagger_ui_html(openapi_url: str, title: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css" />
    <style>
        :root {{
            --fx-bg: #f6f8fb;
            --fx-card: #ffffff;
            --fx-border: #e6eaf0;
            --fx-border-soft: #eef2f6;
            --fx-text: #1f2a37;
            --fx-text-soft: #475467;
            --fx-text-muted: #98a2b3;
            --fx-link: #175cd3;
            --fx-link-hover: #1849a9;
            --fx-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }}

        html, body {{
            margin: 0;
            padding: 0;
            background: var(--fx-bg);
        }}

        body {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            color: var(--fx-text);
        }}

        .swagger-ui {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 16px 12px 28px;
        }}

        .swagger-ui .topbar {{
            display: none;
        }}

        .swagger-ui .information-container {{
            padding-bottom: 4px;
        }}

        .swagger-ui .info {{
            margin: 0 0 14px 0;
        }}

        .swagger-ui .info .title {{
            color: var(--fx-text);
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}

        .swagger-ui .scheme-container {{
            background: transparent;
            box-shadow: none;
            padding: 0;
            margin: 0 0 8px 0;
        }}

        .swagger-ui .opblock-tag-section {{
            margin-bottom: 8px;
            border: 1px solid var(--fx-border);
            border-radius: 12px;
            overflow: hidden;
            background: var(--fx-card);
            box-shadow: var(--fx-shadow);
        }}

        /* 外层三列: tag | description | arrow */
        .swagger-ui .opblock-tag {{
            display: grid !important;
            grid-template-columns: 420px minmax(0, 1fr) 28px;
            column-gap: 18px;
            align-items: center;
            padding: 9px 14px !important;
            margin: 0 !important;
            background: #fff;
            border-bottom: 1px solid var(--fx-border-soft);
        }}

        .swagger-ui .opblock-tag:hover {{
            background: #fafbfc;
        }}

        /* tag 标题 */
        .swagger-ui .opblock-tag .nostyle {{
            grid-column: 1;
            min-width: 0;
            margin: 0;
            white-space: normal !important;
            word-break: break-word;
            overflow-wrap: anywhere;
            line-height: 1.3;
            font-size: 15px !important;
            font-weight: 700 !important;
            color: var(--fx-text) !important;
        }}

        /* description 容器 */
        .swagger-ui .opblock-tag small {{
            grid-column: 2;
            display: block !important;
            min-width: 0;
            margin: 0 !important;
            padding: 0 !important;
            white-space: normal !important;
            color: var(--fx-text-soft) !important;
            font-size: 12.5px !important;
            line-height: 1.45 !important;
        }}

        .swagger-ui .opblock-tag small .markdown {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        .swagger-ui .opblock-tag small .markdown p {{
            margin: 0 !important;
            padding: 0 !important;
        }}

        /* 第一行 description */
        .swagger-ui .opblock-tag small .markdown p:first-child {{
            margin-bottom: 3px !important;
            color: var(--fx-text) !important;
            font-size: 13.5px !important;
            line-height: 1.5 !important;
            letter-spacing: 0.05px;
            max-width: 760px;
        }}

        .swagger-ui .opblock-tag small .markdown p:first-child strong {{
            font-weight: 600 !important;
            color: var(--fx-text) !important;
        }}

        /* 第二行: 作者、版本、Repo */
        .swagger-ui .opblock-tag small .markdown p:last-child {{
            color: var(--fx-text-soft) !important;
            font-size: 12px !important;
            line-height: 1.4 !important;
        }}

        /* Repo 链接 */
        .swagger-ui .opblock-tag small a {{
            color: var(--fx-link);
            text-decoration: none;
            font-weight: 500;
        }}

        .swagger-ui .opblock-tag small a:hover {{
            color: var(--fx-link-hover);
            text-decoration: underline;
        }}

        /* 右侧展开箭头 */
        .swagger-ui .opblock-tag > button {{
            grid-column: 3 !important;
            justify-self: end !important;
            align-self: center !important;
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            width: 24px;
            height: 24px;
        }}

        .swagger-ui .opblock-tag > button svg {{
            display: block !important;
            width: 20px !important;
            height: 20px !important;
            opacity: 0.75;
            transition: all 0.15s ease;
        }}

        .swagger-ui .opblock-tag:hover > button svg {{
            opacity: 1;
            transform: translateX(2px);
        }}

        .swagger-ui .opblock {{
            margin: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }}

        .swagger-ui .opblock:last-child {{
            border-bottom: none !important;
        }}

        .swagger-ui .opblock-summary-path,
        .swagger-ui .opblock-summary-description {{
            white-space: normal !important;
            word-break: break-word;
        }}

        @media (max-width: 1400px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 360px minmax(0, 1fr) 28px;
            }}

            .swagger-ui .opblock-tag small .markdown p:first-child {{
                max-width: 680px;
            }}
        }}

        @media (max-width: 1100px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 300px minmax(0, 1fr) 28px;
                column-gap: 14px;
            }}

            .swagger-ui .opblock-tag small .markdown p:first-child {{
                max-width: none;
            }}
        }}

        @media (max-width: 900px) {{
            .swagger-ui .opblock-tag {{
                grid-template-columns: 1fr;
                row-gap: 6px;
            }}

            .swagger-ui .opblock-tag .nostyle,
            .swagger-ui .opblock-tag small,
            .swagger-ui .opblock-tag > button {{
                grid-column: auto !important;
            }}

            .swagger-ui .opblock-tag > button {{
                justify-self: end !important;
            }}
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>

    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>
    <script>
        window.ui = SwaggerUIBundle({{
            url: "{openapi_url}",
            dom_id: "#swagger-ui",
            deepLinking: true,
            docExpansion: "none",
            defaultModelsExpandDepth: -1,
            displayRequestDuration: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout"
        }});
    </script>
</body>
</html>
        """
    )  # roqa


def build_plugin_description(
    author: str,
    version: str,
    description: str,
    repo: str,
) -> str:
    return f"**{description}**\n\n\n👤 {author} · 🧩 {version} · [🔗 Repo]({repo})"
