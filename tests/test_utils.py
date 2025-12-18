from typing import Any

import pytest
from pydantic import BaseModel

from framex.config import AuthConfig
from framex.utils import StreamEnventType, make_stream_event


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
