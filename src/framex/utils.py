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
