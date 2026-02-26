from fastapi.testclient import TestClient


def test_get_health(client: TestClient):
    """Test the health endpoint."""
    r = client.get("/health").json()
    assert r == "ok"


def test_get_version(client: TestClient):
    """Test the version endpoint."""
    r = client.get("/version")
    assert r.status_code == 200
