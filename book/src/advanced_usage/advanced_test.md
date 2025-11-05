# Simulating Network Communication (For Tests)

This feature is designed **exclusively for tests**.\
When writing unit tests or integration tests that involve HTTP calls, you should avoid calling real external services.\
Instead, use **pytest + VCR** to **record** the first HTTP interaction and **replay** it in subsequent test runs.

______________________________________________________________________

## 1) Why?

- Makes tests **deterministic** (no dependency on unstable external APIs).
- Makes tests **faster** by avoiding repeated network requests.
- Prevents **API quota exhaustion** or accidental use of sensitive credentials.
- Ensures **CI pipelines** run consistently with no external dependencies.

## 2) VCR Configuration (for tests)

In your tests/conftest.py, define fixtures for pytest:

```
@pytest.fixture(scope="module")
def vcr_config():
    return {
        "record_mode": "new_episodes",  # record new calls only when missing
        "filter_headers": ["authorization", "api-key"],  # hide secrets
        "ignore_hosts": ["testserver"],  # don't record FastAPI TestClient
        "match_on": ["uri", "method", "body", "path", "query"],
        "allow_playback_repeats": True,
    }

@pytest.fixture(scope="module")
def disable_recording(request):  # noqa
    return settings.test.disable_record_request

def before_record_request(request):
    # Skip recording noisy or irrelevant endpoints
    if all(ch not in request.path for ch in ["rerank", "minio"]):
        return request
    return None

def before_record_response(response):
    if response["status"]["code"] != 200:
        return None
    return response
```

This ensures only test-related network traffic is recorded and sensitive headers are stripped out.

## 3) Writing Tests with VCR

Annotate your test with @pytest.mark.vcr(...) in need:

```
import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from tests.conftest import before_record_request, before_record_response

@pytest.mark.vcr(before_record_request=before_record_request, before_record_response=before_record_response)
def test_get_proxy_version(client: TestClient):
    res = client.get(f"{API_STR}/base/version").json()
    assert res["status"] == 200
    assert res["data"]
```

The first run will auto record the request and save it into a cassette file under tests/cassettes/. Later runs will replay the response from the cassette, with no real network call.
