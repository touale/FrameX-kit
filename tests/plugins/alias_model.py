from pydantic import BaseModel, ConfigDict, Field

from framex.consts import VERSION
from framex.plugin import BasePlugin, PluginMetadata, on_register, on_request
from framex.plugin.model import ApiType

__plugin_meta__ = PluginMetadata(
    name="alias_demo",
    version=VERSION,
    description="示例: 展示带 alias 的 BaseModel 输入",
    author="alias",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


class UserInfo(BaseModel):
    user_id: int = Field(..., alias="uid")
    user_name: str = Field(..., alias="uname")
    age: int = Field(0)

    model_config = ConfigDict(populate_by_name=True)


@on_register()
class AliasDemoPlugin(BasePlugin):
    @on_request("/alias/info", call_type=ApiType.ALL)
    async def get_user_info(self) -> UserInfo:
        return UserInfo(
            user_id=1,
            user_name="alias",
            age=18,
        )
