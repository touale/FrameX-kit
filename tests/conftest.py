from collections.abc import Generator
from pathlib import Path

import pytest
from click.testing import CliRunner
from fastapi import FastAPI
from fastapi.testclient import TestClient

import framex
from framex.config import settings


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
def disable_recording(request):  # noqa
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
def test_app() -> FastAPI:
    plugins = framex.load_plugins(str(Path(__file__).parent / "plugins"))
    assert len(plugins) == len(["invoker", "export", "alias_model"])
    return framex.run(test_mode=True)  # type: ignore [return-value]


@pytest.fixture(scope="session")
def client(test_app: FastAPI) -> Generator:
    with TestClient(test_app) as c:
        yield c


@pytest.fixture
def runner():
    """Provide a reusable Click CLI runner."""
    return CliRunner()
