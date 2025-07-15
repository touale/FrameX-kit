import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from tests.conftest import before_record_request


@pytest.mark.vcr(before_record_request=before_record_request)
def test_get_proxy_version(client: TestClient):
    res = client.get(f"{API_STR}/base/version").json()
    assert res["status"] == 200
    assert res["data"]
