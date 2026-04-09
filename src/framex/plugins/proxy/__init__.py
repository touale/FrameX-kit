import inspect
import json
from collections.abc import AsyncGenerator, Callable
from typing import Any, cast

import httpx
from pydantic import BaseModel, create_model
from starlette import status
from typing_extensions import override

from framex.adapter import get_adapter
from framex.adapter.base import BaseAdapter
from framex.consts import BACKEND_NAME, PROXY_FUNC_HTTP_PATH, PROXY_PLUGIN_NAME
from framex.log import logger
from framex.plugin import BasePlugin, PluginApi, PluginMetadata, on_register
from framex.plugin.model import ApiType
from framex.plugin.on import on_request
from framex.plugins.proxy.builder import (
    create_pydantic_model,
    format_proxy_params,
    is_upload_annotation,
    resolve_annotation,
    to_multipart_annotation,
    type_map,
)
from framex.plugins.proxy.config import VERSION, ProxyPluginConfig, settings
from framex.plugins.proxy.model import ProxyFunc, ProxyFuncHttpBody
from framex.utils import build_plugin_description, cache_decode, cache_encode, shorten_str

__plugin_meta__ = PluginMetadata(
    name="proxy",
    version=VERSION,
    description="proxy 是 FrameX 的核心系统插件, 作为透明代理转发 API 请求至外部 HTTP 端点并返回响应。",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
    config_class=ProxyPluginConfig,
)


@on_register(**settings.ingress_config)
class ProxyPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        self.func_map: dict[str, Any] = {}
        self.proxy_func_map: dict[str, ProxyFunc] = {}
        self.time_out = settings.timeout
        self.init_proxy_func_route = False
        super().__init__(**kwargs)

    @override
    async def on_start(self) -> None:
        if not settings.proxy_url_list:  # pragma: no cover
            logger.opt(colors=True).warning("<y>No url provided, skipping proxy plugin</y>")
            return

        for url in settings.proxy_url_list:
            logger.info(f"Try to parse openapi docs from {url}")
            await self._parse_openai_docs(url)

        if settings.proxy_functions:
            for url, funcs in settings.proxy_functions.items():
                for func in funcs:
                    await self._parse_proxy_function(func, url)
        else:  # pragma: no cover
            logger.debug("No proxy functions to register")

        logger.success(f"Succeeded to parse openai docs form {url}")

    @on_request(call_type=ApiType.FUNC)
    async def check_is_gen_api(self, path: str) -> bool:
        return path in settings.force_stream_apis

    async def _get_openai_docs(self, url: str, docs_path: str = "/api/v1/openapi.json") -> dict[str, Any]:
        if auth_api_key := settings.auth.get_auth_keys(docs_path):
            headers = {"Authorization": auth_api_key[0]}  # Use the first auth key set
        else:  # pragma: no cover
            headers = None
        async with httpx.AsyncClient(timeout=self.time_out) as client:
            response = await client.get(f"{url}{docs_path}", headers=headers)
            if response.status_code != status.HTTP_200_OK:  # pragma: no cover
                logger.error(
                    f"Failed to get openai docs from {url}, status code: {response.status_code}, response: {response.text}"
                )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    async def _parse_openai_docs(self, url: str) -> None:
        adapter: BaseAdapter = get_adapter()
        openapi_data = await self._get_openai_docs(url)
        paths = openapi_data.get("paths", {})
        components = openapi_data.get("components", {}).get("schemas", {})
        for path, details in paths.items():
            # Check if the path is legal!
            if not settings.is_white_url(url, path):
                logger.opt(colors=True).warning(f"Proxy api(<y>{path}</y>) not in white_list, skipping...")
                continue

            # Get auth api_keys
            if auth_api_key := settings.auth.get_auth_keys(path):
                headers = {"Authorization": auth_api_key[0]}  # Use the first auth key set
                logger.trace(f"Proxy api({path}) requires auth")
            else:
                headers = None

            for method, body in details.items():
                func_name = body.get("operationId")
                # Process request parameters
                params: list[tuple[str, Any]] = [
                    (name, c_type)
                    for param in (body.get("parameters") or [])
                    if (name := param.get("name"))
                    and (typ := param.get("schema").get("type"))
                    and (c_type := type_map.get(typ))
                ]
                body_param_names: set[str] = set()
                file_param_names: set[str] = set()

                # Process request body
                if request_body := body.get("requestBody"):
                    body_content = request_body.get("content", {})
                    if "application/json" in body_content:
                        content_type = "application/json"
                    elif "multipart/form-data" in body_content:
                        content_type = "multipart/form-data"
                    else:
                        logger.opt(colors=True).error(
                            f"Failed to proxy api({method}) <r>{url}{path}</r>, unsupported content type: ${body_content.keys()}"
                        )
                        continue

                    schema = body_content.get(content_type, {}).get("schema", {})
                    if (schema_name := schema.get("$ref", {}).rsplit("/", 1)[-1]) and not (
                        model_schema := components.get(schema_name)
                    ):
                        logger.opt(colors=True).error(
                            f"Failed to proxy api({method}) <r>{url}{path}</r>, schema '{schema_name}' not found in components"
                        )
                        continue

                    if content_type == "application/json":
                        Model = create_pydantic_model(schema_name, model_schema, components)  # noqa
                        params.append(("model", Model))
                        body_param_names.add("model")
                    else:
                        for field_name, prop_schema in model_schema.get("properties", {}).items():
                            annotation = resolve_annotation(prop_schema, components)
                            params.append((field_name, to_multipart_annotation(annotation)))
                            body_param_names.add(field_name)
                            if is_upload_annotation(annotation):
                                file_param_names.add(field_name)

                logger.opt(colors=True).trace(f"Found proxy api({method}) <g>{url}{path}</g>")
                is_stream = path in settings.force_stream_apis
                func = self._create_dynamic_method(
                    func_name,
                    method,
                    params,
                    f"{url}{path}",
                    body_param_names=body_param_names,
                    file_param_names=file_param_names,
                    stream=is_stream,
                    headers=headers,
                )
                setattr(self, func_name, func)

                # Register router
                plugin_api = PluginApi(
                    deployment_name=BACKEND_NAME,
                    func_name="register_route",
                )
                handle = adapter.get_handle(PROXY_PLUGIN_NAME)
                description = build_plugin_description(
                    __plugin_meta__.author,
                    f"v{__plugin_meta__.version}",
                    __plugin_meta__.description,
                    __plugin_meta__.url,
                )
                await adapter.call_func(
                    plugin_api,
                    path=path,
                    methods=[method],
                    func_name=func_name,
                    params=params,
                    handle=handle,
                    stream=is_stream,
                    direct_output=True,
                    tags=[f"{__plugin_meta__.name}({url})"],
                    description=description,
                )

                # Proxy api to map
                self.func_map[path] = func

    async def register_proxy_func_route(
        self,
    ) -> None:
        adapter: BaseAdapter = get_adapter()
        # Register router
        plugin_api = PluginApi(
            deployment_name=BACKEND_NAME,
            func_name="register_route",
        )

        handle = adapter.get_handle(PROXY_PLUGIN_NAME)
        await adapter.call_func(
            plugin_api,
            path=PROXY_FUNC_HTTP_PATH,
            methods=["POST"],
            func_name=self._proxy_func_route.__name__,
            params=[("model", ProxyFuncHttpBody)],
            handle=handle,
            stream=False,
            direct_output=False,
            tags=[__plugin_meta__.name],
            include_in_schema=False,
        )

    async def _proxy_func_route(self, model: ProxyFuncHttpBody) -> Any:
        return await self.call_proxy_function(model.func_name, model.data)

    async def _parse_proxy_function(self, func_name: str, url: str) -> None:
        logger.opt(colors=True).debug(f"Found proxy function <g>{url}</g>")

        params: list[tuple[str, type]] = [("model", ProxyFuncHttpBody)]

        if auth_api_key := settings.auth.get_auth_keys(PROXY_FUNC_HTTP_PATH):
            headers = {"Authorization": auth_api_key[0]}  # Use the first auth key set
            logger.debug(f"Proxy func({PROXY_FUNC_HTTP_PATH}) requires auth")
        else:  # pragma: no cover
            headers = None

        func = self._create_dynamic_method(
            func_name, "POST", params, f"{url}{PROXY_FUNC_HTTP_PATH}", stream=False, headers=headers
        )
        await self.register_proxy_function(func_name, func, is_remote=True)

    async def __call__(self, proxy_path: str, **kwargs: Any) -> Any:
        if func := self.func_map.get(proxy_path):
            return await func(**kwargs)
        raise RuntimeError(f"api({proxy_path}) not found")

    # @logger.catch
    async def fetch_response(
        self,
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None] | dict | str:
        if stream:
            client = httpx.AsyncClient(timeout=self.time_out)

            async def stream_generator() -> AsyncGenerator[str, None]:
                async with client.stream(**kwargs) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        yield chunk
                await client.aclose()

            return stream_generator()
        async with httpx.AsyncClient(timeout=self.time_out) as client:
            response = await client.request(**kwargs)
            response.raise_for_status()
            try:
                return cast(dict, response.json())
            except json.JSONDecodeError:
                return response.text

    def _create_dynamic_method(
        self,
        func_name: str,
        method: str,
        params: list[tuple[str, type]],
        url: str,
        body_param_names: set[str] | None = None,
        file_param_names: set[str] | None = None,
        stream: bool = False,
        headers: dict[str, str] | None = None,
    ) -> Callable[..., Any]:
        # Build a Pydantic request model (for data validation)
        model_name = f"{func_name.title()}_RequestModel"
        RequestModel = create_model(model_name, **{k: (t, ...) for k, t in params})  # type: ignore # noqa
        body_param_names = body_param_names or set()
        file_param_names = file_param_names or set()

        # Construct dynamic methods
        async def dynamic_method(**kwargs: Any) -> AsyncGenerator[str, None] | dict[str, Any] | str:
            log_info = shorten_str(format_proxy_params(**kwargs), 512)
            logger.info(f"Calling proxy url: {url} with kwargs: {log_info}")
            validated = RequestModel(**kwargs)  # Type Validation
            query = {}
            json_body = None
            form_body = {}
            files = []
            for field_name, value in validated:
                if field_name in body_param_names:
                    if field_name == "model" and isinstance(value, BaseModel):
                        json_body = value.model_dump()
                    elif field_name in file_param_names:
                        upload_values = value if isinstance(value, list) else [value]
                        for upload in upload_values:
                            upload.file.seek(0)
                            files.append(
                                (
                                    field_name,
                                    (
                                        upload.filename or field_name,
                                        upload.file,
                                        upload.content_type or "application/octet-stream",
                                    ),
                                )
                            )
                    else:
                        form_body[field_name] = value
                elif isinstance(value, BaseModel):
                    json_body = value.model_dump()
                else:
                    query[field_name] = value
            try:
                request_kwargs: dict[str, Any] = {
                    "stream": stream,
                    "method": method.upper(),
                    "url": url,
                    "params": query,
                    "headers": headers,
                }
                if method.upper() != "GET":
                    if files or form_body:
                        if form_body:
                            request_kwargs["data"] = form_body
                        if files:
                            request_kwargs["files"] = files
                    elif json_body is not None:
                        request_kwargs["json"] = json_body
                return await self.fetch_response(
                    **request_kwargs,
                )
            except Exception as e:
                logger.opt(exception=e, colors=True).error(f"Error calling proxy api({method}) <y>{url}</y>: {e}")
                return "error proxy"

        # Construct a signature and set all parameters as required
        sig = inspect.Signature(
            [
                inspect.Parameter(k, inspect.Parameter.KEYWORD_ONLY, annotation=t, default=inspect.Parameter.empty)
                for k, t in params
            ]
        )
        dynamic_method.__signature__ = sig  # type: ignore
        dynamic_method.__annotations__ = dict(params)
        dynamic_method.__name__ = func_name
        return dynamic_method

    @override
    def _post_call_remote_api_hook(self, data: Any) -> Any:
        return data.get("data") or data

    async def register_proxy_function(
        self, func_name: str, func_callable: Callable[..., Any], is_remote: bool = False
    ) -> bool:
        if not self.init_proxy_func_route:
            await self.register_proxy_func_route()
            self.init_proxy_func_route = True
        if func_name in self.proxy_func_map and not is_remote:
            logger.warning(f"Proxy function {func_name} already registered, skipping...")
            return False

        logger.info(f"Registering proxy function: {func_name}")
        self.proxy_func_map[func_name] = ProxyFunc(func=func_callable, is_remote=is_remote)
        return True

    async def call_proxy_function(self, func_name: str, data: str) -> str:
        decode_func_name = cache_decode(func_name)
        decode_kwargs = cache_decode(data)
        if proxy_func := self.proxy_func_map.get(decode_func_name):
            if proxy_func.is_remote:
                kwargs = {"model": ProxyFuncHttpBody(data=data, func_name=func_name)}
            else:
                kwargs = decode_kwargs
            tag = "remote" if proxy_func.is_remote else "local"
            logger.info(f"Calling proxy function[{tag}]: {decode_func_name}")
            res = await proxy_func.func(**kwargs)
            return res if proxy_func.is_remote else cache_encode(res)
        raise RuntimeError(f"Proxy function({decode_func_name}) not registered")
