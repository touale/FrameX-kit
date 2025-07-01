__version__ = "v1.0"


from ray import serve

from framex.driver import APIIngress
from framex.log import logger as logger


def run():
    logger.debug("Running...")

    # Get all DeploymentHandle

    from framex.plugin import get_all_deployments, get_http_plugin_apis

    deployments = get_all_deployments()
    http_apis = get_http_plugin_apis()

    serve.run(
        APIIngress.bind(deployments=deployments, plugin_apis=http_apis),  # type: ignore
        blocking=True,
        #   _local_testing_mode=True
    )


from framex.plugin import BasePlugin, PluginApi, PluginMetadata, call_remote_api, load_plugin, on_register, on_request

__all__ = [
    "APIIngress",
    "BasePlugin",
    "PluginApi",
    "PluginMetadata",
    "call_remote_api",
    "load_plugin",
    "on_register",
    "on_request",
]
