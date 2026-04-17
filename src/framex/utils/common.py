import inspect
import json
import re
from collections.abc import Callable
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def plugin_to_deployment_name(plugin_name: str, obj_name: str) -> str:
    return f"{plugin_name}.{obj_name}"


def path_to_module_name(path: Path) -> str:
    """Convert path to module name."""
    rel_path = path.resolve().relative_to(Path.cwd().resolve())
    if rel_path.stem == "__init__":
        module_name = ".".join(rel_path.parts[:-1])
    else:
        module_name = ".".join([*rel_path.parts[:-1], rel_path.stem])  # type: ignore[arg-type]
    return module_name.removeprefix("src.")


def escape_tag(s: str) -> str:
    """Escape <tag> like markers used in colored logs."""
    return re.sub(r"</?((?:[fb]g\s)?[^<>\s]*)>", r"\\\g<0>", s)


def extract_method_params(func: Callable) -> list[tuple[str, Any]]:
    sig = inspect.signature(func)
    params: list[tuple[str, Any]] = []
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


def format_uptime(delta: timedelta) -> str:
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
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
