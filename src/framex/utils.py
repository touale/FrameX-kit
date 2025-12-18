import inspect
import json
import re
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from framex.config import settings


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


def get_auth_keys_by_url(url: str) -> list[str] | None:
    auth_config = settings.auth
    is_protected = False
    for rule in auth_config.auth_urls:
        if rule == url:
            is_protected = True
            break
        if rule.endswith("/*") and url.startswith(rule[:-1]):
            is_protected = True
            break

    if not is_protected:
        return None

    if url in auth_config.special_auth_keys:
        return auth_config.special_auth_keys[url]

    matched_keys = None
    matched_len = -1

    for rule, keys in auth_config.special_auth_keys.items():
        if not rule.endswith("/*"):
            continue

        prefix = rule[:-1]
        if url.startswith(prefix) and len(prefix) > matched_len:
            matched_keys = keys
            matched_len = len(prefix)

    if matched_keys is not None:
        return matched_keys

    return auth_config.general_auth_keys
