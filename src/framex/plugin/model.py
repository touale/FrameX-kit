from dataclasses import dataclass, field
from enum import Enum, StrEnum
from types import ModuleType
from typing import Any

from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    name: str = Field(..., description="The name of the plugin")
    version: str = Field(..., description="The version of the plugin")
    description: str = Field(..., description="The description of the plugin")
    author: str = Field(..., description="The author of the plugin")
    url: str = Field(..., description="The url of the plugin")
    required_remote_apis: list[str] = Field([], description="The list of required plugins")
    priority: int = Field(0, description="The priority of the plugin")
    tags: list[str] = Field([], description="The tags of the plugin")
    config_class: type[BaseModel] | None = None


class ApiType(StrEnum):
    FUNC = "func"
    HTTP = "http"
    ALL = "all"
    PROXY = "proxy"


class PluginApi(BaseModel):
    api: str | None = None
    deployment_name: str
    func_name: str = "__call__"
    methods: list[str] = ["POST"]
    params: list[tuple[str, type]] = []
    call_type: ApiType = ApiType.HTTP
    tags: list[str | Enum] | None = None
    stream: bool = False


@dataclass(eq=False)
class PluginDeployment:
    deployment: type[Any]  # type: ignore
    plugin_apis: list[PluginApi]


@dataclass(eq=False)
class Plugin:
    name: str
    module: ModuleType
    module_name: str
    data_dir: str | None = None
    metadata: PluginMetadata | None = None
    deployments: list[PluginDeployment] = field(default_factory=list)
    config: BaseModel | None = None

    @property
    def required_remote_apis(self) -> list[str]:
        return self.metadata.required_remote_apis if self.metadata else []
