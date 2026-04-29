def test_websocket_echo_route(client):
    with client.websocket_connect("/api/v1/ws/echo/lobby") as websocket:
        websocket.send_text('{"message":"hello"}')
        assert websocket.receive_json() == {
            "status": 200,
            "message": "success",
            "data": "lobby:hello",
        }


def test_websocket_invalid_payload_returns_error(client):
    with client.websocket_connect("/api/v1/ws/echo/lobby") as websocket:
        websocket.send_text("not-json")
        assert websocket.receive_json() == {
            "status": 400,
            "message": "WebSocket message must be valid JSON",
        }
