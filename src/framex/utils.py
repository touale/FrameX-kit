import inspect
import json
import re
import zlib
from collections.abc import Callable
from enum import StrEnum
from itertools import cycle
from pathlib import Path
from typing import Any

import cloudpickle  # type: ignore[import-untyped]
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
    packed = cloudpickle.dumps(data)

    compressed = zlib.compress(packed)
    obfuscated = xor_crypt(compressed)
    return obfuscated.hex()


def cache_decode(data: str) -> Any:
    raw = bytes.fromhex(data)
    de_obfuscated = xor_crypt(raw)
    decompressed = zlib.decompress(de_obfuscated)
    return cloudpickle.loads(decompressed)  # nosec S301
