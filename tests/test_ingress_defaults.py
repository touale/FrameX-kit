from unittest.mock import patch

import pytest

from framex import (
    _build_runtime_env_vars,
    _ensure_server_ingress_config,
    _setup_ray_worker,
)
from framex.config import settings
from framex.consts import RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV
from framex.plugin.model import PluginApi


@pytest.fixture(autouse=True)
def reset_runtime_state(monkeypatch):
    import framex.adapter as adapter_module

    adapter_module._adapter = None
    monkeypatch.setattr(settings.server, "use_ray", False)
    monkeypatch.setattr(settings.server, "ingress_config", {})
    yield
    adapter_module._adapter = None


def test_ensure_server_ingress_config_uses_adaptive_default(monkeypatch):
    monkeypatch.setattr(settings, "base_ingress_config", {"max_ongoing_requests": 10})

    http_apis = [PluginApi(deployment_name=f"plugin_{i}") for i in range(30)]

    _ensure_server_ingress_config(http_apis)

    assert settings.server.ingress_config["max_ongoing_requests"] == 300


def test_build_runtime_env_vars_includes_ingress_override(monkeypatch):
    monkeypatch.setattr(settings.server, "ingress_config", {"max_ongoing_requests": 300})

    env_vars = _build_runtime_env_vars("v1.2.3")

    assert env_vars["REVERSION"] == "v1.2.3"
    assert env_vars[RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV] == "300"


def test_ensure_server_ingress_config_keeps_explicit_override(monkeypatch):
    monkeypatch.setattr(settings, "base_ingress_config", {"max_ongoing_requests": 10})
    monkeypatch.setattr(settings.server, "ingress_config", {"max_ongoing_requests": 80})

    http_apis = [PluginApi(deployment_name=f"plugin_{i}") for i in range(30)]

    _ensure_server_ingress_config(http_apis)

    assert settings.server.ingress_config["max_ongoing_requests"] == 80


def test_setup_ray_worker_applies_propagated_ingress_value(monkeypatch):
    monkeypatch.setenv(RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV, "300")

    with patch("framex._setup_sentry"):
        _setup_ray_worker()

    assert settings.server.use_ray is True
    assert settings.server.ingress_config["max_ongoing_requests"] == 300
