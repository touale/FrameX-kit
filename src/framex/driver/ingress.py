import os
import re
from collections.abc import Callable
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from pydantic import create_model
from starlette.routing import Route

from framex.adapter import get_adapter
from framex.consts import BACKEND_NAME
from framex.driver.application import create_fastapi_application
from framex.driver.auth import api_key_header, auth_jwt
from framex.driver.decorator import api_ingress
from framex.log import setup_logger
from framex.plugin.model import ApiType, PluginApi
from framex.utils import escape_tag, shorten_str

app = create_fastapi_application()


@app.get("/health")
async def health() -> str:
    return "ok"


@app.get("/version")
async def version() -> str:

    from framex.config import settings

    return settings.server.reversion or os.getenv("REVERSION") or "unknown"


@api_ingress(app=app, name=BACKEND_NAME)
class APIIngress:
    def __init__(self, deployments: list[Any], plugin_apis: list["PluginApi"]) -> None:
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
        handle: Any,
        stream: bool = False,
        direct_output: bool = False,
        tags: list[str | Enum] | None = None,
        auth_keys: list[str] | None = None,
        include_in_schema: bool = True,
    ) -> bool:
        from framex.log import logger

        if tags is None:
            tags = ["default"]
        if auth_keys is None:
            from framex.config import settings

            auth_keys = settings.auth.get_auth_keys(path)
            logger.trace(f"API({path}) with tags {tags} requires auth_keys {auth_keys}")
        adapter = get_adapter()

        try:
            routes: list[str] = [route.path for route in app.routes if isinstance(route, Route | APIRoute)]
            # logger.warning(f"API({path}) with tags {tags} is already registered, skipping duplicate registration.")
            methods_str = ",".join(m.upper() for m in methods)

            if path in routes:
                logger.opt(colors=True).warning(
                    f"API route already registered: {methods_str:<4} {path[:40] + '...':<45} ({handle.deployment_name})"
                )
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
                logger.trace(f"API({path}) with tags {tags} requires auth.")

                def _verify_api_key(request: Request, api_key: str | None = Depends(api_key_header)) -> None:
                    if (api_key is None or api_key not in auth_keys) and (not auth_jwt(request)):
                        logger.opt(colors=True).error(
                            f"<r>Unauthorized access attempt with API Key({api_key}) for API({path})</r>"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid API Key({api_key}) for API({path})",
                        )

                dependencies.append(Depends(_verify_api_key))

            self.add_api_route(
                path,
                route_handler,
                methods=methods,
                tags=tags,
                response_class=StreamingResponse if stream else JSONResponse,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )
            methods_str = ",".join(m.upper() for m in methods)
            short_path = shorten_str(path)
            logger.opt(colors=True).success(
                f"API route registered: {methods_str:<4} <g>{short_path:<45}</g> ({handle.deployment_name})"
            )
            return True
        except Exception as e:
            logger.opt(exception=e, colors=True).error(
                f'<r>Failed to register api "{escape_tag(path)}" from {handle.deployment_name}</r>'
            )
        return False

    @app.get("/ping")
    async def inner(self) -> str:  # pragma: no cover
        return "pong"

    def __repr__(self):
        return BACKEND_NAME

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        method_set: set[str] = {m.upper() for m in methods} if methods else {"GET"}
        norm_path = re.sub(r"\{[^}]+\}", "{}", path)

        for route in app.routes:
            if (
                isinstance(route, APIRoute)
                and re.sub(r"\{[^}]+\}", "{}", route.path) == norm_path
                and route.methods & method_set
            ):
                raise RuntimeError(f"Duplicate API route: {sorted(method_set)} {norm_path}")

        app.add_api_route(path, endpoint, methods=list(method_set), **kwargs)
