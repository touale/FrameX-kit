from unittest.mock import Mock, patch

from fastapi import FastAPI

from framex.config import settings
from framex.driver.decorator import api_ingress


def _return_class(cls, _app, **deployment_kwargs):
    assert deployment_kwargs
    return cls


def test_api_ingress_uses_server_override(monkeypatch):
    monkeypatch.setattr(settings, "base_ingress_config", {"max_ongoing_requests": 10})
    monkeypatch.setattr(settings.server, "ingress_config", {"max_ongoing_requests": 80})

    app = FastAPI()
    mock_adapter = Mock()
    mock_adapter.to_ingress.side_effect = _return_class

    with patch("framex.driver.decorator.get_adapter", return_value=mock_adapter):

        @api_ingress(app=app, name="api_ingress")
        class TestIngress:
            pass

    _, kwargs = mock_adapter.to_ingress.call_args
    assert kwargs["name"] == "api_ingress"
    assert kwargs["max_ongoing_requests"] == 80


def test_api_ingress_explicit_kwargs_override_server(monkeypatch):
    monkeypatch.setattr(settings, "base_ingress_config", {"max_ongoing_requests": 10})
    monkeypatch.setattr(settings.server, "ingress_config", {"max_ongoing_requests": 80})

    app = FastAPI()
    mock_adapter = Mock()
    mock_adapter.to_ingress.side_effect = _return_class

    with patch("framex.driver.decorator.get_adapter", return_value=mock_adapter):

        @api_ingress(app=app, name="api_ingress", max_ongoing_requests=120)
        class TestIngress:
            pass

    _, kwargs = mock_adapter.to_ingress.call_args
    assert kwargs["max_ongoing_requests"] == 120
