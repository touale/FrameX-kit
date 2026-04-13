# Simulating Network Communication (For Tests)

This feature is designed exclusively for tests.

When writing unit tests or integration tests that involve HTTP calls, you should avoid calling real external services.

Instead, use `pytest-vcr` to record the first HTTP interaction and replay it in subsequent test runs.

## Why Use It

- makes tests deterministic instead of depending on unstable external APIs
- makes tests faster by avoiding repeated network requests
- prevents accidental consumption of API quota or credentials
- keeps CI runs consistent without requiring real upstream services

## VCR Configuration

Put these fixtures in `tests/conftest.py`:

```python
import pytest

from framex.config import settings


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

## Writing A Test

Then annotate the test with `@pytest.mark.vcr(...)`:

```python
import pytest
from fastapi.testclient import TestClient

from framex.consts import API_STR
from tests.conftest import before_record_request, before_record_response


@pytest.mark.vcr(
    before_record_request=before_record_request,
    before_record_response=before_record_response,
)
def test_get_proxy_version(client: TestClient):
    res = client.get(f"{API_STR}/base/version").json()
    assert res["status"] == 200
    assert res["data"]
```

On the first run, VCR records the HTTP interaction.

On later runs, the same response is replayed from the cassette, so the test does not need to call the real upstream service again.

## Rule Of Thumb

Use `pytest-vcr` when a FrameX test depends on HTTP behavior and you want to keep the request path realistic while making repeated runs deterministic.
