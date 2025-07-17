from fastapi import FastAPI

from framex.config import settings
from framex.consts import VERSION
from framex.log import LoguruHandler, logger


def _setup_env() -> None:
    import os

    from framex.consts import DEFAULT_ENV

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)


def _setup_sentry() -> None:  # pragma: no cover
    if settings.sentry.enable and settings.sentry.dsn and settings.sentry.env:
        import sentry_sdk

        sentry_sdk.set_level("info")
        sentry_sdk.utils.logger.handlers = [LoguruHandler()]

        from framex.adapter import get_adapter

        adapter_mode = get_adapter().mode

        sentry_sdk.init(
            dsn=settings.sentry.dsn,
            debug=settings.sentry.debug,
            release=VERSION,
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


def run(*, blocking: bool = True, test_mode: bool = False) -> FastAPI | None:
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
    from framex.driver.ingress import APIIngress

    if settings.server.use_ray:
        # step4: init ray

        import ray
        from ray import serve

        ray.init(
            num_cpus=8,
            dashboard_host=settings.server.dashboard_host,
            dashboard_port=settings.server.dashboard_port,
            configure_logging=False,
            runtime_env={"worker_process_setup_hook": _setup_sentry},
        )
        serve.start(detached=True, http_options={"host": settings.server.host, "port": settings.server.port})
        api_ingress = APIIngress.bind(deployments=deployments, plugin_apis=http_apis)  # type: ignore

        serve.run(
            api_ingress,  # type: ignore
            blocking=blocking,
        )
    else:
        _setup_sentry()

        import uvicorn

        from framex.driver.ingress import APIIngress, app

        api_ingress = APIIngress(deployments=deployments, plugin_apis=http_apis)

        if test_mode:
            return app

        uvicorn.run(
            app,
            host=settings.server.host,
            port=settings.server.port,
            reload=False,
            loop="asyncio",
        )
    return None


from framex.plugin import (
    PluginApi,
    PluginMetadata,
    load_builtin_plugin,
    load_plugins,
    on_register,
    on_request,
)

__all__ = [
    "APIIngress",
    "BasePlugin",
    "PluginApi",
    "PluginMetadata",
    "load_builtin_plugin",
    "load_plugins",
    "logger",
    "on_register",
    "on_request",
]
