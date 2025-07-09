import inspect
import json
import re
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def plugin_to_deployment_name(plugin_name: str, obj_name: str) -> str:
    return f"{plugin_name}.{obj_name}"


def path_to_module_name(path: Path) -> str:
    """Convert path to module name"""
    rel_path = path.resolve().relative_to(Path.cwd().resolve())
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    return ".".join(*rel_path.parts[:-1], rel_path.stem)  # type: ignore


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


def make_stream_event(event_type: StreamEnventType | str, data: str | dict[str, Any] | BaseModel | None) -> str:
    if not data:
        data = {}
    elif isinstance(data, BaseModel):
        data = data.model_dump()
    elif isinstance(data, str):
        data = {"content": data}
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
