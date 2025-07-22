import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from tests.conftest import before_record_request


@pytest.mark.vcr(before_record_request=before_record_request)
def test_evoke_echo(client: TestClient) -> None:
    params = {"message": "hello world"}
    res = client.get(f"{API_STR}/evoke_echo", params=params).json()
    assert res["status"] == 200
    assert res["data"][-1]  # version
    assert res["data"][:4] == [
        params["message"],
        f"原神真好玩呀, {params['message']}",
        f"我是原神哟! 收到您的消息{params['message']}",
        "hello world,{'id': 1, 'name': '原神'}",
    ]
