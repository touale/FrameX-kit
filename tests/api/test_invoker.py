from fastapi.testclient import TestClient

from framex.consts import API_STR


def test_evoke_echo(client: TestClient) -> None:
    params = {"message": "hello world"}
    res = client.get(f"{API_STR}/evoke_echo", params=params).json()
    assert res["status"] == 200
    assert res["data"] == [
        params["message"],
        f"原神真好玩呀, {params['message']}",
        f"我是原神哟! 收到您的消息{params['message']}",
    ]
