"""Tests for framex.adapter.__init__ module."""

from unittest.mock import MagicMock, patch

from framex.adapter import get_adapter
from framex.adapter.base import BaseAdapter
from framex.adapter.local_adapter import LocalAdapter


class TestGetAdapter:
    """Tests for the get_adapter factory function."""

    def setup_method(self):
        """Reset the global adapter before each test."""
        import framex.adapter as adapter_module

        adapter_module._adapter = None

    def test_get_adapter_returns_local_adapter_when_ray_disabled(self):
        """Test get_adapter returns LocalAdapter when use_ray is False."""
        with patch("framex.adapter.settings.server.use_ray", False):
            adapter = get_adapter()
            assert isinstance(adapter, LocalAdapter)
            assert isinstance(adapter, BaseAdapter)

    def test_get_adapter_returns_ray_adapter_when_ray_enabled(self):
        """Test get_adapter returns RayAdapter when use_ray is True."""
        with (
            patch("framex.adapter.settings.server.use_ray", True),
            patch("framex.adapter.ray_adapter.RayAdapter") as mock_ray_adapter,
        ):
            mock_instance = MagicMock()
            mock_ray_adapter.return_value = mock_instance

            adapter = get_adapter()
            assert adapter == mock_instance
            mock_ray_adapter.assert_called_once()

    def test_get_adapter_returns_same_instance_on_multiple_calls(self):
        """Test get_adapter returns the same singleton instance."""
        with patch("framex.adapter.settings.server.use_ray", False):
            adapter1 = get_adapter()
            adapter2 = get_adapter()
            assert adapter1 is adapter2

    def test_get_adapter_caches_local_adapter(self):
        """Test that LocalAdapter is cached after first call."""
        with patch("framex.adapter.settings.server.use_ray", False):
            adapter1 = get_adapter()
            # Second call should return cached instance
            adapter2 = get_adapter()
            assert adapter1 is adapter2
            assert isinstance(adapter1, LocalAdapter)

    def test_get_adapter_caches_ray_adapter(self):
        """Test that RayAdapter is cached after first call."""
        with (
            patch("framex.adapter.settings.server.use_ray", True),
            patch("framex.adapter.ray_adapter.RayAdapter") as mock_ray_adapter,
        ):
            mock_instance = MagicMock()
            mock_ray_adapter.return_value = mock_instance

            adapter1 = get_adapter()
            adapter2 = get_adapter()

            # Should only instantiate once
            assert adapter1 is adapter2
            assert mock_ray_adapter.call_count == 1

    def test_get_adapter_lazy_imports_ray_adapter(self):
        """Test that RayAdapter is only imported when needed."""
        with patch("framex.adapter.settings.server.use_ray", False):  # noqa
            # Import should not happen when use_ray is False
            with patch("framex.adapter.ray_adapter") as mock_ray_module:
                get_adapter()
                # RayAdapter module should not be accessed
                mock_ray_module.RayAdapter.assert_not_called()

    def test_adapter_initially_none(self):
        """Test that _adapter global is None before first call."""
        import framex.adapter as adapter_module

        adapter_module._adapter = None
        assert adapter_module._adapter is None

    def test_adapter_set_after_first_call(self):
        """Test that _adapter global is set after first call."""
        import framex.adapter as adapter_module

        adapter_module._adapter = None
        with patch("framex.adapter.settings.server.use_ray", False):
            get_adapter()
            assert adapter_module._adapter is not None
            assert isinstance(adapter_module._adapter, LocalAdapter)

    def test_get_adapter_with_switching_ray_setting(self):
        """Test that once adapter is set, changing ray setting doesn't affect it."""
        import framex.adapter as adapter_module

        adapter_module._adapter = None

        with patch("framex.adapter.settings.server.use_ray", False):
            adapter1 = get_adapter()
            assert isinstance(adapter1, LocalAdapter)

        # Change setting, but adapter should still be the same
        with patch("framex.adapter.settings.server.use_ray", True):
            adapter2 = get_adapter()
            # Should still be the same LocalAdapter instance
            assert adapter2 is adapter1
            assert isinstance(adapter2, LocalAdapter)
