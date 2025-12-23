from collections.abc import Callable
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader
from pydantic import create_model
from ray.serve.handle import DeploymentHandle
from starlette.routing import Route

from framex.adapter import get_adapter
from framex.consts import BACKEND_NAME
from framex.driver.application import create_fastapi_application
from framex.driver.decorator import api_ingress
from framex.log import setup_logger
from framex.plugin.model import ApiType, PluginApi
from framex.utils import escape_tag

app = create_fastapi_application()
api_key_header = APIKeyHeader(name="Authorization", auto_error=True)


@app.get("/health")
async def health() -> str:
    return "ok"


@api_ingress(app=app, name=BACKEND_NAME)
class APIIngress:
    def __init__(self, deployments: list[DeploymentHandle], plugin_apis: list["PluginApi"]) -> None:
        setup_logger()
        app.state.ingress = self
        self.deployments_dict = {dep.deployment_name: dep for dep in deployments}
        app.state.deployments_dict = self.deployments_dict
        for plugin_api in plugin_apis:
            if (
                plugin_api.api
                and (deployment := self.deployments_dict.get(plugin_api.deployment_name))
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
        params: list[tuple[str, type | Callable]],
        handle: DeploymentHandle,
        stream: bool = False,
        direct_output: bool = False,
        tags: list[str | Enum] | None = None,
        auth_keys: list[str] | None = None,
    ) -> bool:
        from framex.log import logger

        if tags is None:
            tags = ["default"]
        if auth_keys is None:
            from framex.config import settings

            auth_keys = settings.auth.get_auth_keys(path)
            logger.debug(f"API({path}) with tags {tags} requires auth_keys {auth_keys}")
        adapter = get_adapter()

        try:
            routes: list[str] = [route.path for route in app.routes if isinstance(route, Route | APIRoute)]
            if path in routes:
                logger.warning(f"API({path}) with tags {tags} is already registered, skipping duplicate registration.")
                return False
            if (not path) or (not methods):
                raise RuntimeError(f"Api({path}) or methods({methods}) is empty")
            Model: BaseModel = create_model(f"{func_name}_InputModel", **{name: (tp, ...) for name, tp in params})  # type:ignore # noqa

            async def route_handler(response: Response, model: Model = Depends()) -> Any:  # type: ignore [valid-type]
                c_handle = getattr(handle, func_name)
                if not c_handle:
                    raise RuntimeError(
                        f"No handle found for api({methods}): {path} from {handle.deployment_name}.{func_name}"
                    )
                response.headers["X-Raw-Output"] = str(direct_output)
                if stream:
                    gen = adapter._stream_call(c_handle, **(model.__dict__))
                    return StreamingResponse(  # type: ignore
                        gen,
                        media_type="text/event-stream",
                    )
                return await adapter._acall(c_handle, **model.__dict__)  # type: ignore

            # Inject auth dependency if needed
            dependencies = []
            if auth_keys is not None:
                logger.debug(f"API({path}) with tags {tags} requires auth.")

                def _verify_api_key(api_key: str = Depends(api_key_header)) -> None:
                    if api_key not in auth_keys:
                        logger.error(f"Unauthorized access attempt with API Key({api_key}) for API({path})")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid API Key({api_key}) for API({path})",
                        )

                dependencies.append(Depends(_verify_api_key))

            app.add_api_route(
                path,
                route_handler,
                methods=methods,
                tags=tags,
                response_class=StreamingResponse if stream else JSONResponse,
                dependencies=dependencies,
            )
            logger.opt(colors=True).success(
                f"Succeeded to register api({methods}): {path} from {handle.deployment_name}, params: {params}"
            )
            return True
        except Exception as e:
            logger.opt(exception=e).error(f'Failed to register api "{escape_tag(path)}" from {handle.deployment_name}')

        return False

    @app.get("/ping")
    async def inner(self) -> str:  # pragma: no cover
        return "pong"

    def __repr__(self):
        return BACKEND_NAME
