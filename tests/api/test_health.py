from fastapi.testclient import TestClient


def test_get_health(client: TestClient):
    """Test the version endpoint."""
    r = client.get("/health").json()
    assert r == "ok"
