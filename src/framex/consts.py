from enum import StrEnum

PROJECT_NAME = "FrameX"
VERSION = "0.4.0"
API_PRE_STR = "/api"
API_STR = f"{API_PRE_STR}/v1"
OPENAPI_URL = f"{API_STR}/openapi.json"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"

BACKEND_NAME = "backend"
APP_NAME = "default"

PROXY_PLUGIN_NAME = "proxy.ProxyPlugin"
PROXY_FUNC_HTTP_PATH = f"{API_STR}/proxy/remote"

DEFAULT_ENV = {"RAY_COLOR_PREFIX": "1", "RAY_DEDUP_LOGS": "1", "RAY_SERVE_RUN_SYNC_IN_THREADPOOL": "1"}
RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV = "FRAMEX_SERVER_INGRESS_MAX_ONGOING_REQUESTS"

SEBTRY_BLOCK_URLS = [
    "/health",
    "/ping",
]

AUTH_COOKIE_NAME = "framex_token"

CACHE_REQUEST_HEADER = "X-FrameX-Cache"
CACHE_KEY_HEADER = "X-FrameX-Cache-Key"
CACHE_STATUS_HEADER = "X-FrameX-Cache-Status"
SUPPORTED_CACHE_METHODS = {"GET", "POST"}


class CacheAction(StrEnum):
    USE = "use"
    BYPASS = "bypass"
    REFRESH = "refresh"


class CacheStatus(StrEnum):
    DISABLED = "DISABLED"
    BYPASS = "BYPASS"
    HIT = "HIT"
    MISS = "MISS"
    REFRESH = "REFRESH"
