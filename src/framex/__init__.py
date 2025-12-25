from fastapi import FastAPI

from framex.config import settings
from framex.consts import VERSION
from framex.log import LoguruHandler, logger


def _setup_env() -> None:
    import os

    from framex.consts import DEFAULT_ENV

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)


def _setup_sentry(reversion: str | None = None) -> None:  # pragma: no cover
    if settings.sentry.enable and settings.sentry.dsn and settings.sentry.env:
        import sentry_sdk

        sentry_sdk.set_level("info")
        sentry_sdk.utils.logger.handlers = [LoguruHandler()]

        from framex.adapter import get_adapter

        adapter_mode = get_adapter().mode

        import os

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
        )
        logger.success(
            f"Successfully setup sentry with env: {settings.sentry.env}_{adapter_mode}, release: {reversion}"
        )


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
    enable_proxy = enable_proxy if enable_proxy is not None else settings.server.enable_proxy
    builtin_plugins = settings.load_builtin_plugins if load_builtin_plugins is None else load_builtin_plugins
    external_plugins = settings.load_plugins if load_plugins is None else load_plugins

    reversion = reversion or VERSION

    if test_mode and use_ray:
        raise RuntimeError("FlameX can not run when `test_mode` == True, and `use_ray` == True")

    # step1: setup log
    import sys

    from framex.log import StderrFilter

    # logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    sys.stderr = StderrFilter(sys.stderr, "file_system_monitor.cc:116:")

    # step2: setup env
    _setup_env()

    # step 4: setup settings plugins
    # Get all builtin_plugins

    from framex.plugin.load import auto_load_plugins

    auto_load_plugins(builtin_plugins, external_plugins, enable_proxy)

    # step5: init all DeploymentHandle
    logger.info("Start initializing all DeploymentHandle...")
    from framex.plugin import get_http_plugin_apis, init_all_deployments

    deployments = init_all_deployments(enable_proxy=enable_proxy)
    http_apis = get_http_plugin_apis()

    if use_ray:
        # step4: init ray

        import ray
        from ray import serve

        ray.init(
            num_cpus=num_cpus if num_cpus > 0 else None,
            dashboard_host=dashboard_host,
            dashboard_port=dashboard_port,
            configure_logging=False,
            runtime_env={
                "env_vars": {
                    "REVERSION": reversion,
                },
                "worker_process_setup_hook": _setup_sentry,
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

        uvicorn.run(  # pragma: no cover
            app,
            host=server_host,
            port=server_port,
            reload=False,
            loop="asyncio",
        )

    return None  # pragma: no cover


from framex.plugin import (
    BasePlugin,
    PluginApi,
    PluginMetadata,
    get_plugin,
    get_plugin_config,
    load_builtin_plugins,
    load_plugins,
    on_register,
    on_request,
    remote,
)

__all__ = [
    "BasePlugin",
    "PluginApi",
    "PluginMetadata",
    "get_plugin",
    "get_plugin_config",
    "load_builtin_plugins",
    "load_plugins",
    "logger",
    "on_register",
    "on_request",
    "remote",
]
