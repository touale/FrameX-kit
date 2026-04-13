import os
import sys

from fastapi import FastAPI

from framex.config import settings
from framex.consts import RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV, VERSION
from framex.log import LoguruHandler, logger
from framex.plugin.model import PluginApi


def _apply_runtime_env() -> None:
    from framex.consts import DEFAULT_ENV

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)

    if max_ongoing_requests := os.getenv(RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV):
        settings.server.ingress_config["max_ongoing_requests"] = int(max_ongoing_requests)


def _build_runtime_env_vars(reversion: str | None = None) -> dict[str, str]:
    from framex.consts import DEFAULT_ENV

    env_vars = {key: os.getenv(key, value) for key, value in DEFAULT_ENV.items()}
    if reversion:
        env_vars["REVERSION"] = reversion

    max_ongoing_requests = settings.server.ingress_config.get("max_ongoing_requests")
    if isinstance(max_ongoing_requests, int) and max_ongoing_requests > 0:
        env_vars[RAY_INGRESS_MAX_ONGOING_REQUESTS_ENV] = str(max_ongoing_requests)

    return env_vars


def _setup_sentry(reversion: str | None = None) -> None:  # pragma: no cover
    if settings.sentry.enable and settings.sentry.dsn and settings.sentry.env:
        import sentry_sdk

        from framex.consts import SEBTRY_BLOCK_URLS

        def before_send(event, hint):  # noqa
            request = event.get("request")
            if not request:
                return event

            url = request.get("url", "")

            if any(path in url for path in SEBTRY_BLOCK_URLS):
                return None
            return event

        sentry_sdk.set_level("info")
        sentry_sdk.utils.logger.handlers = [LoguruHandler()]

        from framex.adapter import get_adapter

        adapter_mode = get_adapter().mode

        reversion = reversion or os.getenv("REVERSION")

        if reversion and not reversion.startswith("v"):
            reversion = f"v{reversion}"

        sentry_sdk.init(
            dsn=settings.sentry.dsn,
            debug=settings.sentry.debug,
            release=reversion,
            environment=f"{settings.sentry.env}_{adapter_mode}",
            ignore_errors=settings.sentry.ignore_errors,
            include_local_variables=True,
            send_default_pii=True,
            traces_sample_rate=1.0,
            profile_session_sample_rate=1.0,
            profile_lifecycle=settings.sentry.lifecycle,
            _experiments={
                "enable_logs": settings.sentry.enable_logs,
            },
            before_send=before_send,
        )
        logger.success(
            f"Successfully setup sentry with env: {settings.sentry.env}_{adapter_mode}, release: {reversion}"
        )


def _derive_server_ingress_config(http_apis: list[PluginApi]) -> dict[str, int]:
    base_max_ongoing_requests = settings.base_ingress_config.get("max_ongoing_requests")
    if not isinstance(base_max_ongoing_requests, int) or base_max_ongoing_requests <= 0:
        return {}

    deployment_names = {api.deployment_name for api in http_apis if api.deployment_name}
    deployment_count = max(len(deployment_names), 1)

    return {
        "max_ongoing_requests": max(
            base_max_ongoing_requests * 6,
            base_max_ongoing_requests * deployment_count,
        )
    }


def _ensure_server_ingress_config(http_apis: list[PluginApi]) -> None:
    if not settings.server.ingress_config:
        settings.server.ingress_config = _derive_server_ingress_config(http_apis)


def _setup_ray_worker() -> None:  # pragma: no cover
    settings.server.use_ray = True
    _apply_runtime_env()

    import framex.adapter as adapter_module

    adapter_module._adapter = None
    _setup_sentry()


def run(
    *,
    server_host: str | None = None,
    server_port: int | None = None,
    dashboard_host: str | None = None,
    dashboard_port: int | None = None,
    num_cpus: int | None = None,
    use_ray: bool | None = None,
    enable_proxy: bool | None = None,
    load_builtin_plugins: list[str] | None = None,
    load_plugins: list[str] | None = None,
    reversion: str | None = None,
    blocking: bool = True,
    test_mode: bool = False,
) -> FastAPI | None:
    server_host = server_host if server_host is not None else settings.server.host
    server_port = server_port if server_port is not None else settings.server.port
    dashboard_host = dashboard_host if dashboard_host is not None else settings.server.dashboard_host
    dashboard_port = dashboard_port if dashboard_port is not None else settings.server.dashboard_port
    num_cpus = num_cpus if num_cpus is not None else settings.server.num_cpus
    use_ray = use_ray if use_ray is not None else settings.server.use_ray
    settings.server.use_ray = use_ray
    enable_proxy = enable_proxy if enable_proxy is not None else settings.server.enable_proxy
    builtin_plugins = settings.load_builtin_plugins if load_builtin_plugins is None else load_builtin_plugins
    external_plugins = settings.load_plugins if load_plugins is None else load_plugins

    if reversion:
        settings.server.reversion = reversion
    elif settings.server.reversion:
        reversion = settings.server.reversion
    else:
        reversion = VERSION
        settings.server.reversion = VERSION

    if test_mode and use_ray:
        raise RuntimeError("FlameX can not run when `test_mode` == True, and `use_ray` == True")

    from framex.log import StderrFilter

    sys.stderr = StderrFilter(sys.stderr, "file_system_monitor.cc:116:")

    _apply_runtime_env()

    from framex.plugin.load import auto_load_plugins

    auto_load_plugins(builtin_plugins, external_plugins, enable_proxy)

    logger.info("Start initializing all DeploymentHandle...")
    from framex.plugin import get_http_plugin_apis, init_all_deployments

    deployments = init_all_deployments(enable_proxy=enable_proxy)
    http_apis = get_http_plugin_apis()
    _ensure_server_ingress_config(http_apis)

    if use_ray:
        try:
            import ray  # type: ignore[import-not-found]
            from ray import serve  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError(
                'Ray engine requires extra dependency.\nInstall with: uv pip install "framex-kit[ray]"'
            ) from e

        ray.init(
            num_cpus=num_cpus if num_cpus > 0 else None,
            dashboard_host=dashboard_host,
            dashboard_port=dashboard_port,
            configure_logging=False,
            runtime_env={
                "env_vars": _build_runtime_env_vars(reversion),
                "worker_process_setup_hook": _setup_ray_worker,
            },
        )
        serve.start(
            detached=True,
            http_options={"host": server_host, "port": server_port},
        )
        from framex.driver.ingress import APIIngress

        api_ingress = APIIngress.bind(deployments=deployments, plugin_apis=http_apis)  # type: ignore

        serve.run(
            api_ingress,  # type: ignore
            blocking=blocking,
        )
    else:
        _setup_sentry(reversion=reversion)

        import uvicorn

        from framex.driver.ingress import APIIngress, app

        api_ingress = APIIngress(deployments=deployments, plugin_apis=http_apis)

        if test_mode:
            return app

        from framex.log import LOGGING_CONFIG

        uvicorn.run(  # pragma: no cover
            app,
            host=server_host,
            port=server_port,
            reload=False,
            loop="asyncio",
            log_config=LOGGING_CONFIG,
        )

    return None  # pragma: no cover


from framex.plugin import (
    BasePlugin,
    PluginApi,
    PluginMetadata,
    call_plugin_api,
    get_plugin,
    get_plugin_config,
    load_builtin_plugins,
    load_plugins,
    on_proxy,
    on_register,
    on_request,
    register_proxy_func,
    remote,
)

__all__ = [
    "BasePlugin",
    "PluginApi",
    "PluginMetadata",
    "call_plugin_api",
    "get_plugin",
    "get_plugin_config",
    "load_builtin_plugins",
    "load_plugins",
    "logger",
    "on_proxy",
    "on_register",
    "on_request",
    "register_proxy_func",
    "remote",
]
