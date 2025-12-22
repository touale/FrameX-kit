import framex
from framex.consts import VERSION


def test_get_plugin():
    # check simple plugin
    plugin = framex.get_plugin("export")
    assert plugin
    assert plugin.version == VERSION
    assert plugin.name == "export"
    assert plugin.module_name == "tests.plugins.export"

    assert plugin.config
    assert plugin.config.model_dump() == {"id": 123, "name": "test"}


from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from framex.consts import PROXY_PLUGIN_NAME
from framex.plugin import call_plugin_api
from framex.plugin.model import ApiType, PluginApi


class SampleModel(BaseModel):
    """Sample model for testing parameter conversion."""

    field1: str
    field2: int


class TestCallPluginApi:
    """Comprehensive tests for call_plugin_api function with proxy handling."""

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_existing_api(self):
        """Test calling an API that exists in the manager."""
        # Setup
        api = PluginApi(api="test_api", deployment_name="test_deployment", params=[("param1", str), ("param2", int)])

        with (
            patch("framex.plugin._manager.get_api", return_value=api),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value="test_result")

            # Execute
            result = await call_plugin_api("test_api", param1="value1", param2=42)

            # Assert
            assert result == "test_result"
            mock_adapter.return_value.call_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_basemodel_result(self):
        """Test that BaseModel results are converted to dict with aliases."""
        api = PluginApi(api="test_api", deployment_name="test_deployment")
        model_result = SampleModel(field1="test", field2=123)

        with (
            patch("framex.plugin._manager.get_api", return_value=api),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value=model_result)

            result = await call_plugin_api("test_api")

            assert isinstance(result, dict)
            assert result == {"field1": "test", "field2": 123}

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_success(self):
        """Test proxy API call with successful response (status 200)."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            # Simulate proxy response
            proxy_response = {"status": 200, "data": {"result": "proxy_success"}}
            mock_adapter.return_value.call_func = AsyncMock(return_value=proxy_response)

            result = await call_plugin_api("/external/api")

            # Should return just the data field
            assert result == {"result": "proxy_success"}

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_empty_data(self):
        """Test proxy API call that returns empty data with warning."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger") as mock_logger,
        ):
            proxy_response = {"status": 200, "data": None}
            mock_adapter.return_value.call_func = AsyncMock(return_value=proxy_response)

            result = await call_plugin_api("/external/api")

            assert result is None
            # Verify warning was logged
            mock_logger.opt.return_value.warning.assert_called()

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_error_status(self):
        """Test proxy API call with non-200 status logs error."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger") as mock_logger,
        ):
            proxy_response = {"status": 500, "data": None}
            mock_adapter.return_value.call_func = AsyncMock(return_value=proxy_response)
            with pytest.raises(RuntimeError, match="Proxy API /external/api returned status 500"):
                await call_plugin_api("/external/api")

            # Verify error was logged
            mock_logger.opt.return_value.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_plugin_api_not_found_no_proxy(self):
        """Test API not found when proxy is disabled raises RuntimeError."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", False),
            pytest.raises(RuntimeError, match="API test_api is not found"),
        ):
            await call_plugin_api("test_api")

    @pytest.mark.asyncio
    async def test_call_plugin_api_not_found_non_slash_with_proxy(self):
        """Test non-slash prefixed API not found with proxy enabled raises error."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            pytest.raises(RuntimeError, match="API test_api is not found"),
        ):
            await call_plugin_api("test_api")

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_dict_to_basemodel_conversion(self):
        """Test automatic conversion of dict parameters to BaseModel."""
        api = PluginApi(api="test_api", deployment_name="test_deployment", params=[("model_param", SampleModel)])

        with (
            patch("framex.plugin._manager.get_api", return_value=api),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value="success")

            # Pass dict that should be converted to SampleModel
            result = await call_plugin_api("test_api", model_param={"field1": "test", "field2": 456})

            # Verify the call was made and dict was converted
            assert result == "success"
            call_args = mock_adapter.return_value.call_func.call_args
            assert isinstance(call_args[1]["model_param"], SampleModel)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_interval_apis(self):
        """Test using interval_apis parameter to override manager lookup."""
        api = PluginApi(api="test_api", deployment_name="test_deployment")
        interval_apis = {"test_api": api}

        with (
            patch("framex.plugin._manager.get_api") as mock_get_api,
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value="interval_result")

            result = await call_plugin_api("test_api", interval_apis=interval_apis)

            # Manager get_api should not be called
            mock_get_api.assert_not_called()
            assert result == "interval_result"

    @pytest.mark.asyncio
    async def test_call_plugin_api_proxy_creates_correct_plugin_api(self):
        """Test that proxy fallback creates PluginApi with correct parameters."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger"),
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"status": 200, "data": "ok"})

            await call_plugin_api("/proxy/test")

            # Check the PluginApi passed to call_func
            call_args = mock_adapter.return_value.call_func.call_args
            api = call_args[0][0]
            assert isinstance(api, PluginApi)
            assert api.api == "/proxy/test"
            assert api.deployment_name == PROXY_PLUGIN_NAME
            assert api.call_type == ApiType.PROXY

    @pytest.mark.asyncio
    async def test_call_plugin_api_regular_dict_result_not_proxy(self):
        """Test that regular dict results (non-proxy) are returned as-is."""
        api = PluginApi(api="test_api", deployment_name="test_deployment")

        with (
            patch("framex.plugin._manager.get_api", return_value=api),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            # Regular dict result (not from proxy)
            mock_adapter.return_value.call_func = AsyncMock(return_value={"key": "value", "status": 200})

            result = await call_plugin_api("test_api")

            # Should return the entire dict, not extract "data"
            assert result == {"key": "value", "status": 200}

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_multiple_kwargs(self):
        """Test calling API with multiple keyword arguments."""
        api = PluginApi(
            api="test_api", deployment_name="test_deployment", params=[("a", int), ("b", str), ("c", bool)]
        )

        with (
            patch("framex.plugin._manager.get_api", return_value=api),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value="multi_args")

            result = await call_plugin_api("test_api", a=1, b="test", c=True)

            assert result == "multi_args"
            call_kwargs = mock_adapter.return_value.call_func.call_args[1]
            assert call_kwargs["a"] == 1
            assert call_kwargs["b"] == "test"
            assert call_kwargs["c"] is True

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_missing_status(self):
        """Test proxy API call raises when status field is missing."""
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger"),
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"data": "value"})
            with pytest.raises(RuntimeError, match="missing 'status' field"):
                await call_plugin_api("/external/api")
