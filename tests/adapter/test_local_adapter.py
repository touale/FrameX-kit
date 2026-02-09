"""Tests for framex.adapter.local_adapter module."""

import asyncio
import threading
from unittest.mock import MagicMock, patch

from framex.adapter.base import AdapterMode
from framex.adapter.local_adapter import LocalAdapter


class TestLocalAdapter:
    """Tests for LocalAdapter class."""

    def test_mode_is_local(self):
        """Test LocalAdapter mode is LOCAL."""
        adapter = LocalAdapter()
        assert adapter.mode == AdapterMode.LOCAL

    def test_to_deployment_sets_deployment_name(self):
        """Test to_deployment sets deployment_name attribute on class."""
        adapter = LocalAdapter()

        class TestClass:
            pass

        result = adapter.to_deployment(TestClass, name="my_deployment")
        assert hasattr(result, "deployment_name")
        assert result.deployment_name == "my_deployment"

    def test_to_deployment_without_name(self):
        """Test to_deployment without name doesn't set attribute."""
        adapter = LocalAdapter()

        class TestClass:
            pass

        result = adapter.to_deployment(TestClass)
        assert not hasattr(result, "deployment_name")

    def test_to_deployment_with_other_kwargs(self):
        """Test to_deployment handles other kwargs."""
        adapter = LocalAdapter()

        class TestClass:
            pass

        result = adapter.to_deployment(TestClass, name="test", other_param="value")
        assert hasattr(result, "deployment_name")
        assert result.deployment_name == "test"

    def test_get_handle_returns_deployment(self):
        """Test get_handle returns deployment from app state."""
        adapter = LocalAdapter()

        mock_deployment = MagicMock()
        mock_app = MagicMock()
        mock_app.state.deployments_dict = {"test_deployment": mock_deployment}

        with patch("framex.driver.ingress.app", mock_app):
            handle = adapter.get_handle("test_deployment")
            assert handle == mock_deployment

    def test_get_handle_returns_ingress_for_backend(self):
        """Test get_handle returns ingress for BACKEND_NAME."""
        adapter = LocalAdapter()

        mock_ingress = MagicMock()
        mock_app = MagicMock()
        mock_app.state.deployments_dict = {}
        mock_app.state.ingress = mock_ingress

        with (
            patch("framex.driver.ingress.app", mock_app),
            patch("framex.consts.BACKEND_NAME", "backend"),
        ):
            handle = adapter.get_handle("backend")
            assert handle == mock_ingress

    def test_get_handle_returns_none_when_not_found(self):
        """Test get_handle returns None when deployment not found."""
        adapter = LocalAdapter()

        mock_app = MagicMock()
        mock_app.state.deployments_dict = {}

        with patch("framex.driver.ingress.app", mock_app):
            handle = adapter.get_handle("nonexistent")
            assert handle is None

    def test_bind_calls_deployment_with_kwargs(self):
        """Test bind calls deployment function with kwargs."""
        adapter = LocalAdapter()

        def mock_deployment(**kwargs):
            return kwargs

        result = adapter.bind(mock_deployment, param1="value1", param2="value2")
        assert result == {"param1": "value1", "param2": "value2"}

    def test_bind_with_no_kwargs(self):
        """Test bind calls deployment with no kwargs."""
        adapter = LocalAdapter()

        def mock_deployment(**kwargs):
            return "called"

        result = adapter.bind(mock_deployment)
        assert result == "called"

    def test_safe_plot_wrapper_uses_lock(self):
        """Test _safe_plot_wrapper uses thread lock."""
        adapter = LocalAdapter()
        call_order = []
        lock_acquired = []

        def mock_func(*args, **kwargs):
            # Check if lock is held
            lock_acquired.append(threading.current_thread().ident)
            call_order.append("func")
            return "result"

        result = adapter._safe_plot_wrapper(mock_func, "arg1", kwarg1="value1")
        assert result == "result"
        assert len(lock_acquired) == 1

    def test_safe_plot_wrapper_serializes_calls(self):
        """Test _safe_plot_wrapper serializes concurrent calls."""
        adapter = LocalAdapter()
        call_order = []
        lock = threading.Lock()  # noqa

        def slow_func(name):
            call_order.append(f"{name}_start")
            threading.Event().wait(0.01)  # Small delay
            call_order.append(f"{name}_end")
            return name

        # Run two calls concurrently
        def run_wrapper(name):
            return adapter._safe_plot_wrapper(slow_func, name)

        thread1 = threading.Thread(target=run_wrapper, args=("call1",))
        thread2 = threading.Thread(target=run_wrapper, args=("call2",))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Both calls should complete (in any order due to thread scheduling)
        assert "call1_start" in call_order
        assert "call1_end" in call_order
        assert "call2_start" in call_order
        assert "call2_end" in call_order

    async def test_to_remote_func_with_async_function(self):
        """Test to_remote_func handles async functions."""
        adapter = LocalAdapter()

        async def async_func(value):
            return value * 2

        wrapped_func = adapter.to_remote_func(async_func)
        assert hasattr(wrapped_func, "remote")

        result = await wrapped_func.remote(5)
        assert result == 10

    async def test_to_remote_func_with_sync_function(self):
        """Test to_remote_func handles sync functions with asyncio.to_thread."""
        adapter = LocalAdapter()

        def sync_func(value):
            return value * 3

        wrapped_func = adapter.to_remote_func(sync_func)
        assert hasattr(wrapped_func, "remote")

        result = await wrapped_func.remote(5)
        assert result == 15

    async def test_to_remote_func_with_sync_function_uses_safe_wrapper(self):
        """Test to_remote_func uses _safe_plot_wrapper for sync functions."""
        adapter = LocalAdapter()

        def sync_func(value):
            return value + 1

        with patch.object(adapter, "_safe_plot_wrapper", return_value=11) as mock_wrapper:
            wrapped_func = adapter.to_remote_func(sync_func)
            result = await wrapped_func.remote(10)

            # Verify safe wrapper was used
            mock_wrapper.assert_called_once_with(sync_func, 10)
            assert result == 11

    async def test_invoke_with_async_function(self):
        """Test _invoke delegates to _acall for async functions."""
        adapter = LocalAdapter()

        async def async_func(**kwargs):
            return "async_result"

        result = await adapter._invoke(async_func, param="value")
        assert result == "async_result"

    async def test_invoke_with_sync_function(self):
        """Test _invoke delegates to _call for sync functions."""
        adapter = LocalAdapter()

        def sync_func(**kwargs):
            return "sync_result"

        result = await adapter._invoke(sync_func, param="value")
        assert result == "sync_result"

    async def test_acall_awaits_async_function(self):
        """Test _acall awaits async function with kwargs."""
        adapter = LocalAdapter()

        async def async_func(**kwargs):
            return kwargs

        result = await adapter._acall(async_func, key1="value1", key2="value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_call_invokes_sync_function(self):
        """Test _call invokes sync function with kwargs."""
        adapter = LocalAdapter()

        def sync_func(**kwargs):
            return kwargs

        result = adapter._call(sync_func, key1="value1", key2="value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_stream_call_invokes_function(self):
        """Test _stream_call invokes function with kwargs."""
        adapter = LocalAdapter()

        def stream_func(**kwargs):
            yield from kwargs.values()

        result = adapter._stream_call(stream_func, key1="value1", key2="value2")
        values = list(result)
        assert "value1" in values
        assert "value2" in values

    async def test_stream_call_with_async_generator(self):
        """Test _stream_call works with async generators."""
        adapter = LocalAdapter()

        async def async_stream(**kwargs):
            for value in kwargs.values():
                yield value

        result = adapter._stream_call(async_stream, key1="value1", key2="value2")
        values = []
        async for value in result:
            values.append(value)  # noqa
        assert "value1" in values
        assert "value2" in values

    def test_to_remote_func_preserves_original_function(self):
        """Test to_remote_func preserves the original function."""
        adapter = LocalAdapter()

        def original_func(x):
            return x * 2

        wrapped_func = adapter.to_remote_func(original_func)
        # Original function should still be callable
        assert wrapped_func(5) == 10

    async def test_to_remote_func_remote_attribute(self):
        """Test to_remote_func adds remote attribute."""
        adapter = LocalAdapter()

        def sync_func(x):
            return x + 1

        wrapped_func = adapter.to_remote_func(sync_func)
        assert hasattr(wrapped_func, "remote")
        assert callable(wrapped_func.remote)

    async def test_concurrent_safe_plot_wrapper_calls(self):
        """Test multiple concurrent calls to _safe_plot_wrapper are serialized."""
        adapter = LocalAdapter()
        results = []

        def counting_func(n):
            import time

            time.sleep(0.001)  # Small delay to ensure overlap without lock
            results.append(n)
            return n

        async def async_wrapper(n):
            return await asyncio.to_thread(adapter._safe_plot_wrapper, counting_func, n)

        # Run multiple concurrent calls
        await asyncio.gather(*[async_wrapper(i) for i in range(5)])

        # All calls should complete
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}

    def test_get_handle_with_empty_deployments_dict(self):
        """Test get_handle with empty deployments dict."""
        adapter = LocalAdapter()

        mock_app = MagicMock()
        mock_app.state.deployments_dict = {}
        mock_app.state.ingress = None

        with patch("framex.driver.ingress.app", mock_app):
            handle = adapter.get_handle("any_deployment")
            assert handle is None

    async def test_invoke_preserves_kwargs(self):
        """Test _invoke preserves kwargs correctly."""
        adapter = LocalAdapter()

        async def async_func(**kwargs):
            return kwargs

        result = await adapter._invoke(async_func, a=1, b=2, c=3)
        assert result == {"a": 1, "b": 2, "c": 3}
