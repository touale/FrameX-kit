import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from tests.conftest import before_record_request, before_record_response


@pytest.mark.vcr(before_record_request=before_record_request, before_record_response=before_record_response)
def test_evoke_echo(client: TestClient) -> None:
    params = {"message": "hello world"}
    res = client.get(f"{API_STR}/evoke_echo", params=params).json()
    assert res["status"] == 200
    assert res["data"][-1]  # match_result
    assert res["data"][-2]  # version
    assert res["data"][:5] == [
        params["message"],
        f"原神真好玩呀, {params['message']}",
        f"我是原神哟! 收到message={params['message']},call_back_result=hello{params['message']}",
        "hello world,{'id': 1, 'name': '原神'}",
        "remote_sleepremote_func_with_params: 123remote_func_asyncremote_func_async_with_params: 100,abc",
    ]
