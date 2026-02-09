"""Tests for framex.adapter.ray_adapter module."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from framex.adapter.base import AdapterMode


class TestRayAdapterImport:
    """Tests for RayAdapter import error handling."""

    def test_import_error_without_ray(self):
        """Test that importing RayAdapter without ray raises RuntimeError."""
        # Remove ray from sys.modules if it exists
        ray_modules = [key for key in sys.modules if key.startswith("ray")]
        saved_modules = {}
        for mod in ray_modules:
            saved_modules[mod] = sys.modules.pop(mod, None)

        try:
            with patch.dict("sys.modules", {"ray": None, "ray.serve": None}):  # noqa
                with pytest.raises(RuntimeError, match="Ray engine requires extra dependency"):  # noqa
                    # Force reload to trigger ImportError
                    import importlib

                    import framex.adapter.ray_adapter

                    importlib.reload(framex.adapter.ray_adapter)
        finally:
            # Restore modules
            for mod, val in saved_modules.items():
                if val is not None:
                    sys.modules[mod] = val


@pytest.fixture
def mock_ray():
    """Mock ray and ray.serve modules."""
    mock_ray_module = MagicMock()
    mock_serve_module = MagicMock()
    mock_deployment_handle = MagicMock()

    with (
        patch.dict(
            "sys.modules",
            {
                "ray": mock_ray_module,
                "ray.serve": mock_serve_module,
                "ray.serve.handle": MagicMock(DeploymentHandle=mock_deployment_handle),
            },
        ),
        patch("framex.adapter.ray_adapter.ray", mock_ray_module),
        patch("framex.adapter.ray_adapter.serve", mock_serve_module),
        patch("framex.adapter.ray_adapter.DeploymentHandle", mock_deployment_handle),
    ):
        yield mock_ray_module, mock_serve_module, mock_deployment_handle


class TestRayAdapter:
    """Tests for RayAdapter class with mocked ray dependencies."""

    def test_mode_is_ray(self, mock_ray):  # noqa
        """Test RayAdapter mode is RAY."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()
        assert adapter.mode == AdapterMode.RAY

    def test_to_ingress_calls_serve_ingress(self, mock_ray):
        """Test to_ingress calls serve.ingress and to_deployment."""
        from framex.adapter.ray_adapter import RayAdapter

        _, mock_serve_module, _ = mock_ray
        adapter = RayAdapter()

        class TestClass:
            pass

        app = FastAPI()

        # Setup mock chain
        mock_ingress_decorator = MagicMock()
        mock_ingress_result = MagicMock()
        mock_ingress_decorator.return_value = mock_ingress_result
        mock_serve_module.ingress.return_value = mock_ingress_decorator

        mock_deployment_decorator = MagicMock()
        mock_deployment_result = MagicMock()
        mock_deployment_decorator.return_value = mock_deployment_result
        mock_serve_module.deployment.return_value = mock_deployment_decorator

        adapter.to_ingress(TestClass, app, name="test")

        mock_serve_module.ingress.assert_called_once_with(app)
        mock_ingress_decorator.assert_called_once_with(TestClass)
        mock_serve_module.deployment.assert_called_once_with(name="test")

    def test_to_deployment_calls_serve_deployment(self, mock_ray):
        """Test to_deployment calls serve.deployment with kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        _, mock_serve_module, _ = mock_ray
        adapter = RayAdapter()

        class TestClass:
            pass

        mock_decorator = MagicMock()
        mock_result = MagicMock()
        mock_decorator.return_value = mock_result
        mock_serve_module.deployment.return_value = mock_decorator

        adapter.to_deployment(TestClass, name="test", num_replicas=3)

        mock_serve_module.deployment.assert_called_once_with(name="test", num_replicas=3)
        mock_decorator.assert_called_once_with(TestClass)

    def test_to_remote_func_with_sync_function(self, mock_ray):
        """Test to_remote_func wraps sync function with ray.remote."""
        from framex.adapter.ray_adapter import RayAdapter

        mock_ray_module, _, _ = mock_ray
        adapter = RayAdapter()

        def sync_func(x):
            return x * 2

        mock_remote_func = MagicMock()
        mock_ray_module.remote.return_value = mock_remote_func

        result = adapter.to_remote_func(sync_func)

        mock_ray_module.remote.assert_called_once()
        assert result == mock_remote_func

    def test_to_remote_func_with_async_function(self, mock_ray):
        """Test to_remote_func wraps async function to sync then ray.remote."""
        from framex.adapter.ray_adapter import RayAdapter

        mock_ray_module, _, _ = mock_ray
        adapter = RayAdapter()

        async def async_func(x):
            return x * 2

        mock_remote_func = MagicMock()
        mock_ray_module.remote.return_value = mock_remote_func

        result = adapter.to_remote_func(async_func)

        # Should wrap async function and call ray.remote
        mock_ray_module.remote.assert_called_once()
        assert result == mock_remote_func

    def test_to_remote_func_async_wrapper_runs_asyncio(self, mock_ray):
        """Test that async wrapper uses asyncio.run."""
        from framex.adapter.ray_adapter import RayAdapter

        mock_ray_module, _, _ = mock_ray
        adapter = RayAdapter()

        call_log = []

        async def async_func(x):
            call_log.append(f"called with {x}")
            return x * 2

        # Capture the wrapper function passed to ray.remote
        captured_wrapper = None

        def capture_remote(func):
            nonlocal captured_wrapper
            captured_wrapper = func
            return MagicMock()

        mock_ray_module.remote = capture_remote

        adapter.to_remote_func(async_func)

        # Now test the captured wrapper
        assert captured_wrapper is not None
        with patch("asyncio.run") as mock_asyncio_run:
            mock_asyncio_run.return_value = 10
            result = captured_wrapper(5)
            mock_asyncio_run.assert_called_once()
            assert result == 10

    def test_get_handle_calls_serve_get_deployment_handle(self, mock_ray):
        """Test get_handle calls serve.get_deployment_handle."""
        from framex.adapter.ray_adapter import RayAdapter

        _, mock_serve_module, _ = mock_ray
        adapter = RayAdapter()

        mock_handle = MagicMock()
        mock_serve_module.get_deployment_handle.return_value = mock_handle

        with patch("framex.adapter.ray_adapter.APP_NAME", "test_app"):
            result = adapter.get_handle("test_deployment")

        mock_serve_module.get_deployment_handle.assert_called_once_with("test_deployment", app_name="test_app")
        assert result == mock_handle

    def test_bind_calls_deployment_bind(self, mock_ray):  # noqa
        """Test bind calls deployment.bind with kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        mock_deployment = MagicMock()
        mock_bound = MagicMock()
        mock_deployment.bind.return_value = mock_bound

        result = adapter.bind(mock_deployment, param1="value1", param2="value2")

        mock_deployment.bind.assert_called_once_with(param1="value1", param2="value2")
        assert result == mock_bound

    def test_stream_call_uses_options_stream(self, mock_ray):  # noqa
        """Test _stream_call uses options(stream=True).remote."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        mock_func = MagicMock()
        mock_options = MagicMock()
        mock_remote_result = MagicMock()
        mock_func.options.return_value = mock_options
        mock_options.remote.return_value = mock_remote_result

        result = adapter._stream_call(mock_func, param="value")

        mock_func.options.assert_called_once_with(stream=True)
        mock_options.remote.assert_called_once_with(param="value")
        assert result == mock_remote_result

    async def test_acall_awaits_remote(self, mock_ray):
        """Test _acall awaits func.remote."""
        from framex.adapter.ray_adapter import RayAdapter

        _, _, _ = mock_ray
        adapter = RayAdapter()

        mock_func = MagicMock()
        mock_remote = AsyncMock(return_value="result")
        mock_func.remote = mock_remote

        result = await adapter._acall(mock_func, param="value")

        mock_remote.assert_called_once_with(param="value")
        assert result == "result"

    async def test_invoke_with_async_function(self, mock_ray):
        """Test _invoke delegates to _acall for async functions."""
        from framex.adapter.ray_adapter import RayAdapter

        _, _, mock_deployment_handle = mock_ray
        adapter = RayAdapter()

        async def async_func(**kwargs):
            return "async_result"

        # Patch isinstance to always return False for DeploymentHandle check
        with (
            patch(
                "framex.adapter.ray_adapter.isinstance",
                side_effect=lambda obj, cls: False if cls is mock_deployment_handle else isinstance(obj, cls),
            ),
            patch.object(adapter, "_acall", new=AsyncMock(return_value="async_result")) as mock_acall,
        ):
            result = await adapter._invoke(async_func, param="value")
            mock_acall.assert_called_once_with(async_func, param="value")
            assert result == "async_result"

    async def test_invoke_with_deployment_handle(self, mock_ray):
        """Test _invoke delegates to _acall for DeploymentHandle-like object."""
        from framex.adapter.ray_adapter import RayAdapter

        _, _, mock_deployment_handle = mock_ray
        adapter = RayAdapter()

        # Create a mock that will match isinstance check
        # We'll patch inspect.iscoroutinefunction to return False
        # and the isinstance(func, DeploymentHandle) will be checked
        mock_handle = MagicMock()

        with (
            patch("inspect.iscoroutinefunction", return_value=False),
            patch(
                "framex.adapter.ray_adapter.isinstance",
                side_effect=lambda obj, cls: obj is mock_handle and cls is mock_deployment_handle,
            ),
            patch.object(adapter, "_acall", new=AsyncMock(return_value="handle_result")) as mock_acall,
        ):
            result = await adapter._invoke(mock_handle, param="value")
            mock_acall.assert_called_once_with(mock_handle, param="value")
            assert result == "handle_result"

    async def test_invoke_with_sync_function(self, mock_ray):
        """Test _invoke delegates to _call for sync functions."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()
        _, _, mock_deployment_handle = mock_ray

        def sync_func(**kwargs):
            return "sync_result"

        # Patch isinstance to always return False for DeploymentHandle check
        with (
            patch(
                "framex.adapter.ray_adapter.isinstance",
                side_effect=lambda obj, cls: False if cls is mock_deployment_handle else isinstance(obj, cls),
            ),
            patch.object(adapter, "_call", return_value="sync_result") as mock_call,
        ):
            result = await adapter._invoke(sync_func, param="value")
            mock_call.assert_called_once_with(sync_func, param="value")
            assert result == "sync_result"

    def test_call_invokes_function_directly(self, mock_ray):  # noqa
        """Test _call invokes function directly with kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        def mock_func(**kwargs):
            return kwargs

        result = adapter._call(mock_func, key1="value1", key2="value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_bind_with_no_kwargs(self, mock_ray):  # noqa
        """Test bind with no kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        mock_deployment = MagicMock()
        mock_bound = MagicMock()
        mock_deployment.bind.return_value = mock_bound

        result = adapter.bind(mock_deployment)

        mock_deployment.bind.assert_called_once_with()
        assert result == mock_bound

    def test_stream_call_with_multiple_kwargs(self, mock_ray):  # noqa
        """Test _stream_call passes all kwargs correctly."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        mock_func = MagicMock()
        mock_options = MagicMock()
        mock_remote_result = MagicMock()
        mock_func.options.return_value = mock_options
        mock_options.remote.return_value = mock_remote_result

        result = adapter._stream_call(mock_func, a=1, b=2, c=3)

        mock_options.remote.assert_called_once_with(a=1, b=2, c=3)
        assert result == mock_remote_result

    def test_to_deployment_with_no_kwargs(self, mock_ray):
        """Test to_deployment with no kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        _, mock_serve_module, _ = mock_ray
        adapter = RayAdapter()

        class TestClass:
            pass

        mock_decorator = MagicMock()
        mock_result = MagicMock()
        mock_decorator.return_value = mock_result
        mock_serve_module.deployment.return_value = mock_decorator

        adapter.to_deployment(TestClass)

        mock_serve_module.deployment.assert_called_once_with()
        mock_decorator.assert_called_once_with(TestClass)

    async def test_acall_with_no_kwargs(self, mock_ray):  # noqa
        """Test _acall with no kwargs."""
        from framex.adapter.ray_adapter import RayAdapter

        adapter = RayAdapter()

        mock_func = MagicMock()
        mock_remote = AsyncMock(return_value="result")
        mock_func.remote = mock_remote

        result = await adapter._acall(mock_func)

        mock_remote.assert_called_once_with()
        assert result == "result"

    def test_get_handle_with_different_app_name(self, mock_ray):
        """Test get_handle uses APP_NAME constant correctly."""
        from framex.adapter.ray_adapter import RayAdapter

        _, mock_serve_module, _ = mock_ray
        adapter = RayAdapter()

        mock_handle = MagicMock()
        mock_serve_module.get_deployment_handle.return_value = mock_handle

        with patch("framex.adapter.ray_adapter.APP_NAME", "custom_app"):
            result = adapter.get_handle("my_deployment")

        mock_serve_module.get_deployment_handle.assert_called_once_with("my_deployment", app_name="custom_app")
        assert result == mock_handle
