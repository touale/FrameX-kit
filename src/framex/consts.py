PROJECT_NAME = "FrameX"
VERSION = "0.2.6"
API_STR = "/api/v1"
OPENAPI_URL = "/api/v1/openapi.json"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"

BACKEND_NAME = "backend"
APP_NAME = "default"

PROXY_PLUGIN_NAME = "proxy.ProxyPlugin"
PROXY_FUNC_HTTP_PATH = f"{API_STR}/proxy/remote"

DEFAULT_ENV = {"RAY_COLOR_PREFIX": "1", "RAY_DEDUP_LOGS": "1", "RAY_SERVE_RUN_SYNC_IN_THREADPOOL": "1"}
