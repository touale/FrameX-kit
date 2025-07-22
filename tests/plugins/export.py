from pydantic import BaseModel

from framex.consts import VERSION
from framex.plugin.model import PluginMetadata


class ExportPluginConfig(BaseModel):
    id: int = 123
    name: str = "test"


__plugin_meta__ = PluginMetadata(
    name="测试插件",
    version=VERSION,
    description="测试插件元信息",
    author="测试",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
    config_class=ExportPluginConfig,
)
