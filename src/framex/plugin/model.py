from collections.abc import Callable
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
    priority: int = 0
    tags: list[str] = Field(default_factory=list, description="The tags of the plugin")
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
    params: list[tuple[str, type | Callable]] = []
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
    metadata: PluginMetadata | None = None
    deployments: list[PluginDeployment] = field(default_factory=list)

    @property
    def config(self) -> BaseModel | None:
        from framex.plugin import check_plugin_config_exists, get_plugin_config

        if not (self.metadata and self.metadata.config_class):
            return None
        name = self.name if check_plugin_config_exists(self.name) else self.metadata.name
        return (
            get_plugin_config(name, self.metadata.config_class)
            if self.metadata and self.metadata.config_class
            else None
        )

    @property
    def required_remote_apis(self) -> list[str]:
        return self.metadata.required_remote_apis if self.metadata else []

    @property
    def version(self) -> str:
        if self.metadata:
            return self.metadata.version
        return "unknown"
