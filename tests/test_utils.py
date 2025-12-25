import json
from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import BaseModel

from framex.config import AuthConfig
from framex.utils import StreamEnventType, cache_decode, cache_encode, format_uptime, make_stream_event


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


def test_is_url_protected():
    cfg = AuthConfig(
        rules={
            "/api/user": ["k1"],
            "/api/*": ["k2"],
        }
    )

    assert cfg._is_url_protected("/api/user")
    assert cfg._is_url_protected("/api/user/1")
    assert not cfg._is_url_protected("/admin")


def test_get_auth_keys():
    cfg = AuthConfig(
        rules={
            "/api/*": ["k1"],
            "/api/admin/*": ["k2"],
            "/api/admin/user": ["k3"],
        }
    )

    assert cfg.get_auth_keys("/public") is None
    assert cfg.get_auth_keys("/api/user") == ["k1"]
    assert cfg.get_auth_keys("/api/admin/test") == ["k2"]
    assert cfg.get_auth_keys("/api/admin/user") == ["k3"]


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


def test_format_uptime():
    """Test format_uptime function"""
    # Test seconds only
    delta = timedelta(seconds=45)
    assert format_uptime(delta) == "45s"

    # Test minutes and seconds
    delta = timedelta(seconds=125)
    assert format_uptime(delta) == "2m 5s"

    # Test hours, minutes, and seconds
    delta = timedelta(seconds=3665)
    assert format_uptime(delta) == "1h 1m 5s"

    # Test days
    delta = timedelta(days=2, seconds=3661)
    assert format_uptime(delta) == "2d 1h 1m 1s"

    # Test zero seconds
    delta = timedelta(seconds=0)
    assert format_uptime(delta) == "0s"

    # Test only minutes (no seconds)
    delta = timedelta(minutes=5, seconds=0)
    assert format_uptime(delta) == "5m"
