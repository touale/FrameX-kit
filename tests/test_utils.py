import json
from typing import Any

import pytest
from pydantic import BaseModel

from framex.config import AuthConfig
from framex.utils import StreamEnventType, cache_decode, cache_encode, make_stream_event


class StreamDataModel(BaseModel):
    content: str
    id: int


@pytest.mark.parametrize(
    ("event_type", "data", "result"),
    [
        ("event a", "data a", 'event: event a\ndata: {"content": "data a"}\n\n'),
        (
            StreamEnventType.MESSAGE_CHUNK,
            {"result": "chunk data"},
            'event: message_chunk\ndata: {"result": "chunk data"}\n\n',
        ),
        (
            StreamEnventType.DEBUG,
            StreamDataModel(content="data a", id=1),
            'event: debug\ndata: {"content": "data a", "id": 1}\n\n',
        ),
    ],
)
def test_make_stream_event(event_type: StreamEnventType | str, data: str | dict[str, Any] | BaseModel, result: str):
    res = make_stream_event(event_type, data)
    assert res == result


def test_get_auth_keys_by_url():
    auth = AuthConfig(
        general_auth_keys=["g"],
        auth_urls=["/api/v1/*", "/api/v2/echo", "/api/v3/*"],
        special_auth_keys={
            "/api/v1/echo": ["s"],
            "/api/v3/echo/*": ["b"],
            "/api/v3/echo/hi": ["c"],
        },
    )

    assert auth.get_auth_keys("/health") is None
    assert auth.get_auth_keys("/api/v1/user") == ["g"]
    assert auth.get_auth_keys("/api/v1/echo") == ["s"]
    assert auth.get_auth_keys("/api/v1/echo/sub") == ["g"]
    assert auth.get_auth_keys("/api/v2/echo") == ["g"]
    assert auth.get_auth_keys("/api/v2/echo/sub") is None
    assert auth.get_auth_keys("/api/v3/sub") == ["g"]
    assert auth.get_auth_keys("/api/v3/echo/1") == ["b"]
    assert auth.get_auth_keys("/api/v3/echo/hi") == ["c"]


from datetime import datetime
from typing import Any

import pytest
from pydantic import BaseModel


class SubModel(BaseModel):
    id: int
    name: str


class ExchangeModel(BaseModel):
    id: str
    name: int
    model: SubModel
    created_at: datetime


def test_basic_types():
    data = {"a": 1, "b": "string", "c": [1, 2, 3], "d": {"nested": True}}
    encoded = cache_encode(data)
    decoded = cache_decode(encoded)
    assert decoded == data
    assert isinstance(decoded["c"], list)


def test_datetime_and_enum():
    now = datetime(2025, 12, 23, 10, 0, 0)
    data = {"time": now}
    encoded = cache_encode(data)
    decoded = cache_decode(encoded)
    assert "2025-12-23T10:00:00" in str(decoded["time"])


def test_nested_pydantic_models():
    sub = SubModel(id=1, name="sub_name")
    main = ExchangeModel(id="main_id", name=100, model=sub, created_at=datetime.now())

    original_data = {"status": "success", "result_list": [main, main], "single_model": main}

    encoded = cache_encode(original_data)
    assert isinstance(encoded, str)

    decoded = cache_decode(encoded)

    res_model = decoded["single_model"]
    assert res_model.id == "main_id"
    assert res_model.name == 100

    assert isinstance(res_model.model, SubModel)
    assert res_model.model.id == 1
    assert res_model.model.name == "sub_name"

    assert decoded["result_list"][0].model.id == 1


def test_recovery_failure_fallback():
    fake_payload = {
        "__type__": "dynamic_obj",
        "__module__": "non.existent.module",
        "__class__": "MissingClass",
        "data": {"id": 999, "info": "test"},
    }
    encoded = json.dumps(fake_payload)
    decoded = cache_decode(encoded)

    assert decoded.id == 999
    assert decoded.info == "test"
