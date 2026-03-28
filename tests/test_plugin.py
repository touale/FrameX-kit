import inspect
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

import framex
from framex.consts import PROXY_PLUGIN_NAME, VERSION
from framex.plugin import call_plugin_api
from framex.plugin.model import ApiType, PluginApi
from framex.plugin.resolver import reset_current_remote_apis, set_current_remote_apis


def test_get_plugin():
    plugin = framex.get_plugin("export")
    assert plugin
    assert plugin.version == VERSION
    assert plugin.name == "export"
    assert plugin.module_name == "tests.plugins.export"

    assert plugin.config
    assert plugin.config.model_dump() == {"id": 123, "name": "test"}


class SampleModel(BaseModel):
    field1: str
    field2: int


class TestCallPluginApi:
    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_success(self):
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"status": 200, "data": {"result": "ok"}})
            result = await call_plugin_api("/external/api")
            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_empty_data(self):
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger") as mock_logger,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"status": 200, "data": None})
            result = await call_plugin_api("/external/api")
            assert result is None
            mock_logger.opt.return_value.warning.assert_called()

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_error_status(self):
        with (
            patch("framex.plugin._manager.get_api", return_value=None),
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger") as mock_logger,
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"status": 500, "data": None})
            with pytest.raises(RuntimeError, match="Proxy API /external/api returned status 500"):
                await call_plugin_api("/external/api")
            mock_logger.opt.return_value.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_plugin_api_not_found_no_proxy(self):
        with (
            patch("framex.plugin.settings.server.enable_proxy", False),
            pytest.raises(RuntimeError, match="API test_api is not found"),
        ):
            await call_plugin_api("test_api")

    @pytest.mark.asyncio
    async def test_call_plugin_api_not_found_non_slash_with_proxy(self):
        with (
            patch("framex.plugin.settings.server.enable_proxy", True),
            pytest.raises(RuntimeError, match="API test_api is not found"),
        ):
            await call_plugin_api("test_api")

    @pytest.mark.asyncio
    async def test_call_plugin_api_requires_remote_apis_in_context(self):
        token = set_current_remote_apis({})
        try:
            with pytest.raises(RuntimeError, match="not declared in current plugin remote_apis"):
                await call_plugin_api("test_api")
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_remote_apis_dict_to_basemodel_conversion(self):
        api = PluginApi(api="test_api", deployment_name="test_deployment", params=[("model_param", SampleModel)])
        token = set_current_remote_apis({"test_api": api})
        try:
            with patch("framex.plugin.get_adapter") as mock_adapter:
                mock_adapter.return_value.call_func = AsyncMock(return_value="success")
                result = await call_plugin_api("test_api", model_param={"field1": "test", "field2": 456})
                assert result == "success"
                call_args = mock_adapter.return_value.call_func.call_args
                assert isinstance(call_args[1]["model_param"], SampleModel)
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_remote_apis(self):
        api = PluginApi(api="test_api", deployment_name="test_deployment")
        token = set_current_remote_apis({"test_api": api})
        try:
            with (
                patch("framex.plugin._manager.get_api") as mock_get_api,
                patch("framex.plugin.get_adapter") as mock_adapter,
            ):
                mock_adapter.return_value.call_func = AsyncMock(return_value="remote_result")
                result = await call_plugin_api("test_api")
                mock_get_api.assert_not_called()
                assert result == "remote_result"
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_remote_apis_dict_payload(self):
        api = PluginApi(api="test_api", deployment_name="test_deployment")
        token = set_current_remote_apis({"test_api": api.model_dump()})
        try:
            with (
                patch("framex.plugin._manager.get_api") as mock_get_api,
                patch("framex.plugin.get_adapter") as mock_adapter,
            ):
                mock_adapter.return_value.call_func = AsyncMock(return_value="remote_dict_result")
                result = await call_plugin_api("test_api")
                mock_get_api.assert_not_called()
                assert result == "remote_dict_result"
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_context_wrapper_preserves_async_generator(self):
        from framex.plugin.base import BasePlugin
        from framex.plugin.on import on_request

        class DemoPlugin(BasePlugin):
            @on_request("/demo", stream=True)
            async def stream_api(self):
                yield "a"
                yield "b"

        plugin = DemoPlugin()
        stream = plugin.stream_api()

        assert inspect.isasyncgen(stream)
        assert [chunk async for chunk in stream] == ["a", "b"]

    @pytest.mark.asyncio
    async def test_call_remote_api_uses_whitelist_via_request_context(self):
        from framex.plugin.base import BasePlugin
        from framex.plugin.on import on_request

        api = PluginApi(api="test_api", deployment_name="test_deployment", params=[("model_param", SampleModel)])

        class DemoPlugin(BasePlugin):
            @on_request("/demo")
            async def request_api(self):
                return await self._call_remote_api("test_api", model_param={"field1": "test", "field2": 456})

        plugin = DemoPlugin(remote_apis={"test_api": api})

        with patch("framex.plugin.get_adapter") as mock_adapter:
            mock_adapter.return_value.call_func = AsyncMock(return_value="success")
            result = await plugin.request_api()
            assert result == "success"
            call_args = mock_adapter.return_value.call_func.call_args
            assert isinstance(call_args[0][0], PluginApi)
            assert isinstance(call_args[1]["model_param"], SampleModel)

    @pytest.mark.asyncio
    async def test_call_remote_api_rejects_missing_whitelist_entry_via_request_context(self):
        from framex.plugin.base import BasePlugin
        from framex.plugin.on import on_request

        class DemoPlugin(BasePlugin):
            @on_request("/demo")
            async def request_api(self):
                return await self._call_remote_api("test_api")

        plugin = DemoPlugin(remote_apis={})

        with pytest.raises(RuntimeError, match="not declared in current plugin remote_apis"):
            await plugin.request_api()

    @pytest.mark.asyncio
    async def test_call_plugin_api_proxy_creates_correct_plugin_api(self):
        with (
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger"),
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"status": 200, "data": "ok"})
            await call_plugin_api("/proxy/test")
            api = mock_adapter.return_value.call_func.call_args[0][0]
            assert isinstance(api, PluginApi)
            assert api.api == "/proxy/test"
            assert api.deployment_name == PROXY_PLUGIN_NAME
            assert api.call_type == ApiType.PROXY

    @pytest.mark.asyncio
    async def test_call_plugin_api_regular_dict_result_not_proxy(self):
        api = PluginApi(api="test_api", deployment_name="test_deployment")
        token = set_current_remote_apis({"test_api": api})
        try:
            with patch("framex.plugin.get_adapter") as mock_adapter:
                mock_adapter.return_value.call_func = AsyncMock(return_value={"key": "value", "status": 200})
                result = await call_plugin_api("test_api")
                assert result == {"key": "value", "status": 200}
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_multiple_kwargs(self):
        api = PluginApi(
            api="test_api", deployment_name="test_deployment", params=[("a", int), ("b", str), ("c", bool)]
        )
        token = set_current_remote_apis({"test_api": api})
        try:
            with patch("framex.plugin.get_adapter") as mock_adapter:
                mock_adapter.return_value.call_func = AsyncMock(return_value="multi_args")
                result = await call_plugin_api("test_api", a=1, b="test", c=True)
                assert result == "multi_args"
                call_kwargs = mock_adapter.return_value.call_func.call_args[1]
                assert call_kwargs["a"] == 1
                assert call_kwargs["b"] == "test"
                assert call_kwargs["c"] is True
        finally:
            reset_current_remote_apis(token)

    @pytest.mark.asyncio
    async def test_call_plugin_api_with_proxy_missing_status(self):
        with (
            patch("framex.plugin.settings.server.enable_proxy", True),
            patch("framex.plugin.get_adapter") as mock_adapter,
            patch("framex.plugin.logger"),
        ):
            mock_adapter.return_value.call_func = AsyncMock(return_value={"data": "value"})
            with pytest.raises(RuntimeError, match="missing 'status' field"):
                await call_plugin_api("/external/api")
