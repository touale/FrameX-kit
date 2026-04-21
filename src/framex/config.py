import secrets
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
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
    ignored_contains: tuple[str, ...] = ("GET /ping", "GET /health")


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
    ingress_config: dict[str, Any] = Field(default_factory=dict)
    reversion: str = ""


class TestConfig(BaseModel):
    disable_record_request: bool = False
    silent: bool = False


class OauthConfig(BaseModel):
    provider: str = ""
    client_id: str = ""
    client_secret: str = ""
    authorization_url: str = ""
    redirect_uri: str = ""
    base_url: str = ""

    token_url: str = ""
    user_info_url: str = ""
    app_url: str = ""

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"

    @property
    def call_back_url(self) -> str:
        return f"{self.app_url}{self.redirect_uri}"

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        if not self.authorization_url:
            self.authorization_url = f"{self.base_url}/oauth/authorize"
        if not self.token_url:
            self.token_url = f"{self.base_url}/oauth/token"
        if not self.user_info_url:
            self.user_info_url = f"{self.base_url}/api/v4/user"
        if not self.jwt_secret:
            self.jwt_secret = secrets.token_urlsafe(32)


class RepositoryProviderAuthConfig(BaseModel):
    token: str = ""
    token_header: str = "Authorization"  # noqa
    token_scheme: str = "Bearer"  # noqa

    def build_headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        if self.token_scheme:
            return {self.token_header: f"{self.token_scheme} {self.token}"}
        return {self.token_header: self.token}


class GitLabRepositoryAuthEndpointConfig(RepositoryProviderAuthConfig):
    host: str
    path_prefix: str = ""
    token_header: str = "PRIVATE-TOKEN"  # noqa
    token_scheme: str = ""

    def matches(self, host: str, path: str) -> bool:
        normalized_prefix = self.normalized_path_prefix
        if self.host.lower() != host.lower():
            return False
        if not normalized_prefix:
            return True
        return path == normalized_prefix or path.startswith(f"{normalized_prefix}/")

    @property
    def normalized_path_prefix(self) -> str:
        if not self.path_prefix:
            return ""
        return self.path_prefix if self.path_prefix.startswith("/") else f"/{self.path_prefix}"


class GitLabRepositoryAuthConfig(RepositoryProviderAuthConfig):
    token_header: str = "PRIVATE-TOKEN"  # noqa
    token_scheme: str = ""
    endpoints: list[GitLabRepositoryAuthEndpointConfig] = Field(default_factory=list)

    def configured_hosts(self) -> set[str]:
        return {endpoint.host.lower() for endpoint in self.endpoints}

    def build_headers_for_url(self, host: str, path: str) -> dict[str, str]:
        if endpoint := self.resolve_endpoint(host, path):
            return endpoint.build_headers()
        return self.build_headers()

    def resolve_endpoint(self, host: str, path: str) -> GitLabRepositoryAuthEndpointConfig | None:
        matches = [endpoint for endpoint in self.endpoints if endpoint.matches(host, path)]
        if not matches:
            return None
        return max(matches, key=lambda endpoint: len(endpoint.normalized_path_prefix))


class RepositoryAuthConfig(BaseModel):
    github: RepositoryProviderAuthConfig = Field(default_factory=RepositoryProviderAuthConfig)
    gitlab: GitLabRepositoryAuthConfig = Field(default_factory=GitLabRepositoryAuthConfig)


class RepositoryConfig(BaseModel):
    auth: RepositoryAuthConfig = Field(default_factory=RepositoryAuthConfig)


class DocsActionButtonInputConfig(BaseModel):
    name: str
    label: str
    placeholder: str = ""
    default: str = ""
    required: bool = False
    target: Literal["body", "query"] = "body"


class DocsActionButtonNoAuthConfig(BaseModel):
    type: Literal["none"] = "none"


class DocsActionButtonOAuthAuthConfig(BaseModel):
    type: Literal["oauth"] = "oauth"
    allowed_usernames: list[str] = Field(default_factory=lambda: ["*"])


class DocsActionButtonPasswordAuthConfig(BaseModel):
    type: Literal["password"] = "password"
    password: str


DocsActionButtonAuthConfig = Annotated[
    DocsActionButtonNoAuthConfig | DocsActionButtonOAuthAuthConfig | DocsActionButtonPasswordAuthConfig,
    Field(discriminator="type"),
]


class DocsActionButtonConfig(BaseModel):
    title: str
    variant: Literal["default", "primary", "success", "warning", "danger"] = "default"
    requires_confirmation: bool = False
    confirmation_message: str = ""
    url: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    query: dict[str, Any] = Field(default_factory=dict)
    body_type: Literal["json", "form"] = "json"
    body: dict[str, Any] = Field(default_factory=dict)
    inputs: list[DocsActionButtonInputConfig] = Field(default_factory=list)
    auth: DocsActionButtonAuthConfig = Field(default_factory=DocsActionButtonNoAuthConfig)


class DocsConfig(BaseModel):
    embedded_config_file_whitelist: list[str] = Field(default_factory=list)
    action_buttons: list[DocsActionButtonConfig] = Field(default_factory=list)


class AuthConfig(BaseModel):
    oauth: OauthConfig | None = Field(default=None)
    rules: dict[str, list[str]] = Field(default_factory=dict)

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
    base_ingress_config: dict[str, Any] = Field(default_factory=lambda: {"max_ongoing_requests": 10})

    server: ServerConfig = Field(default_factory=ServerConfig)
    log: LogConfig = Field(default_factory=LogConfig)

    # plugins config
    plugins: dict[str, Any] = Field(default_factory=dict)
    load_plugins: list[str] = Field(default_factory=list)
    load_builtin_plugins: list[str] = Field(default_factory=list)

    test: TestConfig = Field(default_factory=TestConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)

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
