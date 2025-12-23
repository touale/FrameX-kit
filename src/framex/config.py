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
    legal_proxy_code: list[int] = [200]
    num_cpus: int = -1
    excluded_log_paths: list[str] = []
    ingress_config: dict[str, Any] = {"max_ongoing_requests": 60}

    # docs config
    docs_user: str = "admin"
    docs_password: str = ""

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.docs_password == "":
            key = str(uuid4())
            self.docs_password = key
            from framex.log import logger

            logger.warning(f"No docs_password set, generate a random key: {key}")
        return self


class TestConfig(BaseModel):
    disable_record_request: bool = False
    silent: bool = False


class AuthConfig(BaseModel):
    general_auth_keys: list[str] = Field(default_factory=list)
    auth_urls: list[str] = Field(default_factory=list)
    special_auth_keys: dict[str, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_and_validate(self) -> Self:
        if PROXY_FUNC_HTTP_PATH not in self.auth_urls:
            self.auth_urls.append(PROXY_FUNC_HTTP_PATH)
        if not self.general_auth_keys:  # pragma: no cover
            from framex.log import logger

            key = str(uuid4())
            logger.warning(f"No general_auth_keys set, generate a random key: {key}")
            self.general_auth_keys = [key]
        for special_url in self.special_auth_keys:
            if not self._is_url_protected(special_url):
                raise ValueError(f"special_auth_keys url '{special_url}' is not covered by any auth_urls rule")
        return self

    def _is_url_protected(self, url: str) -> bool:
        """Check if a URL is protected by any auth_urls rule."""
        for rule in self.auth_urls:
            if rule == url:
                return True
            if rule.endswith("/*") and url.startswith(rule[:-1]):
                return True
        return False

    def get_auth_keys(self, url: str) -> list[str] | None:
        is_protected = self._is_url_protected(url)

        if not is_protected:
            return None

        if url in self.special_auth_keys:
            return self.special_auth_keys[url]

        matched_keys = None
        matched_len = -1

        for rule, keys in self.special_auth_keys.items():
            if not rule.endswith("/*"):
                continue

            prefix = rule[:-1]
            if url.startswith(prefix) and len(prefix) > matched_len:
                matched_keys = keys
                matched_len = len(prefix)

        if matched_keys is not None:
            return matched_keys

        return self.general_auth_keys


class Settings(BaseSettings):
    # Global config
    base_ingress_config: dict[str, Any] = {"max_ongoing_requests": 10}

    server: ServerConfig = ServerConfig()
    log: LogConfig = LogConfig()

    # plugins config
    plugins: dict[str, Any] = {}

    # allow load plugins
    load_plugins: list[str] = []
    load_builtin_plugins: list[str] = []

    test: TestConfig = TestConfig()
    sentry: SentryConfig = SentryConfig()
    auth: AuthConfig = AuthConfig()

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
