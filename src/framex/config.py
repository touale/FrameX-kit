from typing import Any

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


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
            TomlConfigSettingsSource(settings_cls),
            PyprojectTomlConfigSettingsSource(settings_cls),
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()
