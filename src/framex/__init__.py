import ray
from ray import serve

from framex.driver import APIIngress
from framex.log import logger


def run() -> None:
    # step1: setup log
    import logging
    import sys

    from framex.log import LoguruHandler, StderrFilter

    logging.basicConfig(handlers=[LoguruHandler()], level=0, force=True)
    sys.stderr = StderrFilter(sys.stderr, "file_system_monitor.cc:116:")

    # step2: setup env
    import os

    from framex.consts import DEFAULT_ENV

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)

    # step4: init ray
    from framex.config import settings

    ray.init(
        num_cpus=8,
        dashboard_host=settings.server.dashboard_host,
        dashboard_port=settings.server.dashboard_port,
        configure_logging=False,
    )

    # step5: init all DeploymentHandle
    logger.info("Start initializing all DeploymentHandle...")
    from framex.plugin import get_http_plugin_apis, init_all_deployments

    deployments = init_all_deployments()
    http_apis = get_http_plugin_apis()

    serve.run(
        APIIngress.bind(deployments=deployments, plugin_apis=http_apis),  # type: ignore
        blocking=True,
        #   _local_testing_mode=True
    )


from framex.plugin import (
    PluginApi,
    PluginMetadata,
    call_remote_api,
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
    "call_remote_api",
    "load_builtin_plugin",
    "load_plugins",
    "logger",
    "on_register",
    "on_request",
]
