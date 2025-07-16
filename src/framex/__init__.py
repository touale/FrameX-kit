from fastapi import FastAPI

from framex.log import logger


def _set_env() -> None:
    import os

    from framex.consts import DEFAULT_ENV

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)


def run(*, blocking: bool = True, test_mode: bool = False) -> FastAPI | None:
    # step1: setup log
    import logging
    import sys

    from framex.config import settings
    from framex.log import LoguruHandler, StderrFilter

    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    sys.stderr = StderrFilter(sys.stderr, "file_system_monitor.cc:116:")

    # step2: setup env
    _set_env()

    # step 4: setup settings plugins
    from framex.plugin.load import load_from_settings

    load_from_settings()

    # step5: init all DeploymentHandle
    logger.info("Start initializing all DeploymentHandle...")
    from framex.plugin import get_http_plugin_apis, init_all_deployments

    deployments = init_all_deployments()
    http_apis = get_http_plugin_apis()
    from framex.driver.ingress import APIIngress

    if settings.use_ray:
        # step4: init ray

        import ray
        from ray import serve

        ray.init(
            num_cpus=8,
            dashboard_host=settings.server.dashboard_host,
            dashboard_port=settings.server.dashboard_port,
            configure_logging=False,
        )
        serve.start(detached=True, http_options={"host": settings.server.host, "port": settings.server.port})
        api_ingress = APIIngress.bind(deployments=deployments, plugin_apis=http_apis)  # type: ignore

        serve.run(
            api_ingress,  # type: ignore
            blocking=blocking,
        )
    else:
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
