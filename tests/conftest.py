from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from fastapi import FastAPI
from fastapi.testclient import TestClient

import framex
from framex.config import settings
from tests.mock import mock_get, mock_request


@pytest.fixture(autouse=True)
def reset_runtime_state(monkeypatch):
    import framex.adapter as adapter_module

    adapter_module._adapter = None
    monkeypatch.setattr(settings.server, "use_ray", False)
    yield
    adapter_module._adapter = None


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "record_mode": "new_episodes",  # new_episodes
        "filter_headers": ["authorization", "api-key"],
        "ignore_hosts": ["testserver"],
        "match_on": ["uri", "method", "body", "path", "query"],
        "allow_playback_repeats": True,
    }


@pytest.fixture(scope="module")
def disable_recording(request):
    return settings.test.disable_record_request


def before_record_request(request):
    if all(
        ch not in request.path
        for ch in [
            "rerank",
            "minio",
        ]
    ):
        return request
    return None


def before_record_response(response):
    if response["status"]["code"] != 200:
        return None
    return response


@pytest.fixture(scope="session", autouse=True)
def test_app() -> Generator:
    plugins = framex.load_plugins(str(Path(__file__).parent / "plugins"))
    assert len(plugins) == len(["invoker", "export", "alias_model"])

    with (
        patch("httpx.AsyncClient.get", new=mock_get),
        patch("httpx.AsyncClient.request", new=mock_request),
    ):
        yield framex.run(test_mode=True)  # type: ignore[return-value]


@pytest.fixture(scope="session")
def client(test_app: FastAPI) -> Generator:
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def runner():
    """Provide a reusable Click CLI runner."""
    return CliRunner()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    try:
        from coverage import Coverage
    except ImportError:
        return

    coverage_dir = Path(".coverage")
    if not coverage_dir.exists():
        return

    data_files = list(coverage_dir.glob(".coverage.*"))
    if not data_files:
        return

    cov = Coverage(config_file=True, data_file=str(coverage_dir / ".coverage"))
    cov.load()
    cov.combine()
    cov.save()
