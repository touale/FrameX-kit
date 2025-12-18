from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from framex.config import AuthConfig
from framex.utils import StreamEnventType, get_auth_keys_by_url, make_stream_event


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

    with patch("framex.utils.settings.auth", auth):
        assert get_auth_keys_by_url("/health") is None
        assert get_auth_keys_by_url("/api/v1/user") == ["g"]
        assert get_auth_keys_by_url("/api/v1/echo") == ["s"]
        assert get_auth_keys_by_url("/api/v1/echo/sub") == ["g"]
        assert get_auth_keys_by_url("/api/v2/echo") == ["g"]
        assert get_auth_keys_by_url("/api/v2/echo/sub") is None
        assert get_auth_keys_by_url("/api/v3/sub") == ["g"]
        assert get_auth_keys_by_url("/api/v3/echo/1") == ["b"]
        assert get_auth_keys_by_url("/api/v3/echo/hi") == ["c"]
