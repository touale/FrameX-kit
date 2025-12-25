from typing import Any, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from framex.consts import PROXY_FUNC_HTTP_PATH


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
    ignore_errors: list[str] = Field(default_factory=list)
    lifecycle: Literal["manual", "trace"] = "manual"
    enable_logs: bool = False


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8080
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8260
    use_ray: bool = False
    enable_proxy: bool = False
    legal_proxy_code: list[int] = Field(default_factory=lambda: [200])
    num_cpus: int = -1
    excluded_log_paths: list[str] = Field(default_factory=list)
    ingress_config: dict[str, Any] = Field(default_factory=lambda: {"max_ongoing_requests": 60})

    # docs config
    docs_user: str = "admin"
    docs_password: str = ""

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover
        if self.docs_password == "":
            self.docs_password = "admin"  # noqa: S105
            from framex.log import logger

            logger.warning("No docs_password set, fallback to default password: admin")


class TestConfig(BaseModel):
    disable_record_request: bool = False
    silent: bool = False


class AuthConfig(BaseModel):
    rules: dict[str, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_and_validate(self) -> Self:
        if PROXY_FUNC_HTTP_PATH not in self.rules:
            key = str(uuid4())
            self.rules[PROXY_FUNC_HTTP_PATH] = [key]
            from framex.log import logger

            logger.warning(
                f"No auth key found for {PROXY_FUNC_HTTP_PATH}. A random key {key} was generated. "
                "Please configure auth.rules explicitly in production.",
            )
        return self

    def _is_url_protected(self, url: str) -> bool:
        for rule in self.rules:
            if rule == url:
                return True
            if rule.endswith("/*") and url.startswith(rule[:-1]):
                return True
        return False

    def get_auth_keys(self, url: str) -> list[str] | None:
        if not self._is_url_protected(url):
            return None

        if url in self.rules:
            return self.rules[url]

        matched_keys = None
        matched_len = -1

        for rule, keys in self.rules.items():
            if not rule.endswith("/*"):
                continue

            prefix = rule[:-1]
            if url.startswith(prefix) and len(prefix) > matched_len:
                matched_keys = keys
                matched_len = len(prefix)

        return matched_keys


class Settings(BaseSettings):
    # Global config
    base_ingress_config: dict[str, Any] = {"max_ongoing_requests": 10}

    server: ServerConfig = Field(default_factory=ServerConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    # plugins config
    plugins: dict[str, Any] = Field(default_factory=dict)
    load_plugins: list[str] = Field(default_factory=list)
    load_builtin_plugins: list[str] = Field(default_factory=list)

    test: TestConfig = Field(default_factory=TestConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

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
            TomlConfigSettingsSource(settings_cls),
            PyprojectTomlConfigSettingsSource(settings_cls),
            init_settings,
            file_secret_settings,
        )


settings = Settings()
