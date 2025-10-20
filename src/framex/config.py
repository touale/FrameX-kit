from pathlib import Path
from typing import Any, Literal

import tomli
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
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
            if plugin_dir.is_dir() and (name := plugin_dir.name.split("@")[0]):
                for file in plugin_dir.iterdir():
                    if not file.is_file():
                        continue
                    if file.stem.lower() != "config":
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


class SentryConfig(BaseModel):
    enable: bool = False
    dsn: str = ""
    env: str = ""  # local, prod, dev
    debug: bool = False
    ignore_errors: list[str] = []
    lifecycle: Literal["manual", "trace"] = "manual"
    enable_logs: bool = False


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8260
    use_ray: bool = False
    enable_proxy: bool = False
    num_cpus: int = 8


class TestConfig(BaseModel):
    disable_record_request: bool = False
    silent: bool = False


class Settings(BaseSettings):
    server: ServerConfig = ServerConfig()
    log: LogConfig = LogConfig()

    # plugins config
    plugins: dict[str, Any] = {}

    # allow load plugins
    load_plugins: list[str] = []
    load_builtin_plugins: list[str] = []

    # dir
    data_dir: Path = Path("data")

    test: TestConfig = TestConfig()

    sentry: SentryConfig = SentryConfig()

    model_config = SettingsConfigDict(
        # `.env.prod` takes priority over `.env`
        env_file=(".env", ".env.prod"),
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        pyproject_toml_table_header=("tool", "framex"),
        toml_file="config.toml",
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
            dotenv_settings,
            PluginConfigSource(settings_cls),
            TomlConfigSettingsSource(settings_cls),
            PyprojectTomlConfigSettingsSource(settings_cls),
            init_settings,
            file_secret_settings,
        )


settings = Settings()
