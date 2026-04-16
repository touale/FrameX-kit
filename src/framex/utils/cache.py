import base64
import importlib
import json
import zlib
from datetime import datetime
from enum import Enum
from itertools import cycle
from typing import Any


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
