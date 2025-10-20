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
    reversion: str | None = None,
    blocking: bool = True,
    test_mode: bool = False,
    num_cpus: int | None = None,
) -> FastAPI | None:
    reversion = reversion or VERSION

    if test_mode and settings.server.use_ray:
        raise RuntimeError("FlameX can not run when `test_mode` == True, and `use_ray` == True")

    # step1: setup log
    import sys

    from framex.log import StderrFilter

    # logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    sys.stderr = StderrFilter(sys.stderr, "file_system_monitor.cc:116:")

    # step2: setup env
    _setup_env()

    # step 4: setup settings plugins
    from framex.plugin.load import load_from_settings

    load_from_settings(settings=settings)

    # step5: init all DeploymentHandle
    logger.info("Start initializing all DeploymentHandle...")
    from framex.plugin import get_http_plugin_apis, init_all_deployments

    deployments = init_all_deployments(enable_proxy=settings.server.enable_proxy)
    http_apis = get_http_plugin_apis()

    if settings.server.use_ray:
        # step4: init ray

        import ray
        from ray import serve

        ray.init(
            num_cpus=num_cpus or settings.server.num_cpus,
            dashboard_host=settings.server.dashboard_host,
            dashboard_port=settings.server.dashboard_port,
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
            http_options={"host": server_host or settings.server.host, "port": server_port or settings.server.port},
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
            host=settings.server.host,
            port=settings.server.port,
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
