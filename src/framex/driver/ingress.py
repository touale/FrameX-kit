import logging
from enum import Enum
from typing import Any

from fastapi import Depends, Response
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from pydantic import create_model
from ray import serve
from ray.serve.handle import DeploymentHandle
from starlette.routing import Route

from framex.consts import BACKEND_NAME
from framex.driver.application import create_fastapi_application
from framex.log import LoguruHandler
from framex.plugin.model import ApiType, PluginApi
from framex.utils import escape_tag

app = create_fastapi_application()


@serve.deployment(
    name=BACKEND_NAME,
    # ray_actor_options={"num_cpus": 0.3},
)
@serve.ingress(app)
class APIIngress:
    def __init__(self, deployments: list[DeploymentHandle], plugin_apis: list["PluginApi"]) -> None:
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).handlers = [LoguruHandler()]

        deployments_dict = {dep.deployment_name: dep for dep in deployments}

        for plugin_api in plugin_apis:
            if (
                plugin_api.api
                and (deployment := deployments_dict.get(plugin_api.deployment_name))
                and plugin_api.call_type
                in [
                    ApiType.HTTP,
                    ApiType.ALL,
                ]
            ):
                self.register_route(
                    plugin_api.api,
                    plugin_api.methods,
                    plugin_api.func_name,
                    plugin_api.params,
                    deployment,
                    stream=plugin_api.stream,
                    direct_output=False,
                    tags=plugin_api.tags,
                )

    def register_route(
        self,
        path: str,
        methods: list[str],
        func_name: str,
        params: list[tuple[str, type]],
        handle: DeploymentHandle,
        stream: bool = False,
        direct_output: bool = False,
        tags: list[str | Enum] | None = None,
    ) -> None:
        if tags is None:
            tags = ["default"]

        from framex.log import logger

        try:
            routes: list[str] = [route.path for route in app.routes if isinstance(route, Route | APIRoute)]

            if path in routes:
                logger.warning(
                    f"API({path}) with tags {tags} is already registered in {routes}, skipping duplicate registration."
                )
                return

            if (not path) or (not methods):
                raise RuntimeError(f"Api({path}) or methods({methods}) is empty")

            Model: BaseModel = create_model(f"{func_name}_InputModel", **{name: (tp, ...) for name, tp in params})  # type:ignore # noqa

            async def route_handler(response: Response, model: Model = Depends()) -> Any:  # type: ignore
                c_handle = getattr(handle, func_name)
                if not c_handle:
                    raise RuntimeError(
                        f"No handle found for api({methods}): {path} from {handle.deployment_name}.{func_name}"
                    )

                response.headers["X-Raw-Output"] = str(direct_output)

                if stream:
                    gen = c_handle.options(stream=stream).remote(**(model.__dict__))
                    return StreamingResponse(  # type: ignore
                        gen,
                        media_type="text/event-stream",
                    )
                return await c_handle.remote(**(model.__dict__))  # type: ignore

            app.add_api_route(path, route_handler, methods=methods, tags=tags)

            logger.opt(colors=True).debug(
                f"Succeeded to register api({methods}): {path} from {handle.deployment_name}"
            )

        except Exception as e:
            logger.opt(exception=e).error(f'Failed to register api "{escape_tag(path)}" from {handle.deployment_name}')

    @app.get("/health")
    async def health(self, response: Response) -> str:
        response.headers["X-Health-Check"] = "Passed"
        return "ok"

    def __repr__(self):
        return BACKEND_NAME
