from pathlib import Path
from typing import Any

import tomli
import yaml
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    YamlConfigSettingsSource,
)


class PluginConfigSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: type[BaseSettings], data_dir: Path = Path("data")):
        super().__init__(settings_cls)
        self.data_dir = data_dir
        self._data: dict[str, Any] = self._load_plugins()

    def _load_plugins(self) -> dict[str, Any]:
        plugin_configs: dict[str, dict] = {}

        if not self.data_dir.is_dir():
            return {}

        for plugin_dir in self.data_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            name = plugin_dir.name.split("@")[0]
            for file in plugin_dir.iterdir():
                if file.suffix in (".yaml", ".yml"):
                    with file.open("r", encoding="utf-8") as f:
                        plugin_configs[name] = yaml.safe_load(f)
                    break
                if file.suffix == ".toml":
                    with file.open("rb") as f:
                        plugin_configs[name] = tomli.load(f)
                    break
        return {"plugins": plugin_configs}

    def __call__(self) -> dict[str, Any]:
        return self._data

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        raise NotImplementedError


class LogConfig(BaseModel):
    simple_log: bool = True
    ignored_prefixes: tuple[str, ...] = (
        "Started executing request to method",
        "CALL register_route",
        "CALL /api/v1",
        "Initialized DeploymentHandle",
        "Finished initializing replica",
        "Got updated replicas for",
        "Started <ray.serve._private.router.SharedRouterLongPollClient object",
    )


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080

    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8260


class Settings(BaseSettings):
    server: ServerConfig = ServerConfig()
    enable_proxy: bool = False
    plugins: dict[str, Any] = {}
    log: LogConfig = LogConfig()
    load_plugins: list[str] = []
    load_builtin_plugins: list[str] = []

    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod"),
        extra="ignore",
        case_sensitive=True,
        pyproject_toml_table_header=("tool", "framex"),
        toml_file="config.toml",
        yaml_file="config.yaml",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            env_settings,
            PluginConfigSource(settings_cls),
            TomlConfigSettingsSource(settings_cls),
            YamlConfigSettingsSource(settings_cls),
            PyprojectTomlConfigSettingsSource(settings_cls),
            dotenv_settings,
            init_settings,
            file_secret_settings,
        )


settings = Settings()
