from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class ProxyFunc(BaseModel):
    func: Callable[..., Any]
    is_remote: bool = False


class ProxyFuncHttpBody(BaseModel):
    data: str
    func_name: str
