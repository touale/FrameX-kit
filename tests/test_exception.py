import pytest

import framex
from framex.plugin.model import PluginApi


def test_run_raises_when_test_mode_and_use_ray(monkeypatch):
    """Test that run() raises RuntimeError when test_mode=True and use_ray=True."""
    from framex.config import settings

    monkeypatch.setattr(settings.server, "use_ray", True)
    with pytest.raises(expected_exception=RuntimeError) as excinfo:
        framex.run(test_mode=True)
    assert "FlameX can not run when `test_mode` == True, and `use_ray` == True" in str(excinfo.value)


async def test_call_not_exist_plugin() -> None:
    from framex.plugin import call_plugin_api

    with pytest.raises(expected_exception=RuntimeError) as excinfo:
        await call_plugin_api(api_name="/call_not_exist_plugin")
    assert "not found" in str(excinfo.value)

    with pytest.raises(expected_exception=RuntimeError) as excinfo:
        await call_plugin_api(api_name="func.call_not_exist_plugin")
    assert "API func.call_not_exist_plugin is not found" in str(excinfo.value)

    with pytest.raises(expected_exception=RuntimeError) as excinfo:
        await call_plugin_api(
            api_name="/call_not_exist_plugin",
            interval_apis={"/call_not_exist_plugin": PluginApi(deployment_name="deployment_name")},
        )
    assert "No handle or function found for deployment(deployment_name:__call__)" in str(excinfo.value)
