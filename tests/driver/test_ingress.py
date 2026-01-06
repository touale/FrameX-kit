from unittest.mock import Mock, patch

import pytest
from fastapi.routing import APIRoute
from starlette.routing import Route

from framex.driver.ingress import APIIngress

# ---------- helpers ----------


def make_route(path: str, methods: set[str]) -> APIRoute:
    route = Mock(spec=APIRoute)
    route.path = path
    route.methods = methods
    return route


# ---------- fixtures ----------


@pytest.fixture
def mock_app():
    with patch("framex.driver.ingress.app") as app:
        app.routes = []
        app.add_api_route = Mock()
        yield app


@pytest.fixture
def ingress():
    return APIIngress.__new__(APIIngress)


# ---------- tests ----------


def test_add_first_route_success(ingress, mock_app):
    endpoint = Mock()

    ingress.add_api_route("/users", endpoint, methods=["GET"])

    mock_app.add_api_route.assert_called_once_with("/users", endpoint, methods=["GET"])


@pytest.mark.parametrize(
    ("existing_path", "new_path"),
    [
        ("/users/{id}", "/users/{id}"),
        ("/users/{id}", "/users/{user_id}"),
        ("/users/{uid}/posts/{pid}", "/users/{id}/posts/{post_id}"),
    ],
)
def test_duplicate_path_same_method_raises(ingress, mock_app, existing_path, new_path):
    mock_app.routes = [make_route(existing_path, {"GET"})]

    with pytest.raises(RuntimeError, match=r"Duplicate API route"):
        ingress.add_api_route(new_path, Mock(), methods=["GET"])


def test_same_path_different_method_allowed(ingress, mock_app):
    mock_app.routes = [make_route("/users/{id}", {"GET"})]

    ingress.add_api_route("/users/{id}", Mock(), methods=["POST"])

    mock_app.add_api_route.assert_called_once()


def test_overlapping_methods_raises(ingress, mock_app):
    mock_app.routes = [make_route("/users", {"GET", "POST"})]

    with pytest.raises(RuntimeError):
        ingress.add_api_route("/users", Mock(), methods=["POST", "PUT"])


def test_case_insensitive_methods(ingress, mock_app):
    mock_app.routes = [make_route("/users", {"GET"})]

    with pytest.raises(RuntimeError):
        ingress.add_api_route("/users", Mock(), methods=["get"])


def test_non_api_route_is_ignored(ingress, mock_app):
    non_api_route = Mock(spec=Route)
    non_api_route.path = "/users/{id}"
    mock_app.routes = [non_api_route]

    ingress.add_api_route("/users/{id}", Mock(), methods=["GET"])

    mock_app.add_api_route.assert_called_once()


def test_kwargs_are_passed_through(ingress, mock_app):
    ingress.add_api_route(
        "/users",
        Mock(),
        methods=["GET"],
        tags=["users"],
        response_class=Mock(),
    )

    _, kwargs = mock_app.add_api_route.call_args
    assert kwargs["tags"] == ["users"]
    assert "response_class" in kwargs
