from dataclasses import dataclass, field
from enum import StrEnum
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


class ApiType(StrEnum):
    FUNC = "func"
    HTTP = "http"
    ALL = "all"


class PluginApi(BaseModel):
    api: str | None = None
    deployment_name: str
    func_name: str
    methods: list[str]
    params: list[tuple[str, type]]
    call_type: ApiType = ApiType.HTTP


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
    def required_remote_apis(self) -> list[str]:
        return self.metadata.required_remote_apis if self.metadata else []
