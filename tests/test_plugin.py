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
