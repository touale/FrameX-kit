import inspect
import json
from collections.abc import AsyncGenerator, Callable
from typing import Any, cast

import httpx
from pydantic import BaseModel, create_model
from typing_extensions import override

from framex.adapter import get_adapter
from framex.adapter.base import BaseAdapter
from framex.consts import BACKEND_NAME, PROXY_PLUGIN_NAME, VERSION
from framex.log import logger
from framex.plugin import BasePlugin, PluginApi, PluginMetadata, on_register
from framex.plugin.model import ApiType
from framex.plugin.on import on_request
from framex.plugins.proxy.builder import create_pydantic_model, type_map
from framex.plugins.proxy.config import ProxyPluginConfig, settings

__plugin_meta__ = PluginMetadata(
    name="proxy",
    version=VERSION,
    description="一个特殊的 framx proxy 插件, 充当透明代理。"
    "它接收 API 请求并将其转发到已配置的外部 HTTP 端点,并将响应返回给调用者。",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
    config_class=ProxyPluginConfig,
)


@on_register(**settings.ingress_config)
class ProxyPlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        self.func_map: dict[str, Any] = {}
        self.time_out = settings.timeout
        super().__init__(**kwargs)

    @override
    async def on_start(self) -> None:
        if not settings.proxy_urls:
            logger.opt(colors=True).warning("<y>No url provided, skipping proxy plugin</y>")
            return
        for url in settings.proxy_urls:
            await self._parse_openai_docs(url)
        logger.success(f"Succeeded to parse openai docs form {url}")

    @on_request(call_type=ApiType.FUNC)
    async def check_is_gen_api(self, path: str) -> bool:
        return path in settings.force_stream_apis

    async def _get_openai_docs(self, url: str) -> dict[str, Any]:
        clent = httpx.AsyncClient(timeout=self.time_out)
        response = await clent.get(f"{url}/api/v1/openapi.json")
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def _parse_openai_docs(self, url: str) -> None:
        adapter: BaseAdapter = get_adapter()
        openapi_data = await self._get_openai_docs(url)
        paths = openapi_data.get("paths", {})
        components = openapi_data.get("components", {}).get("schemas", {})
        for path, details in paths.items():
            # Check if the path is legal!
            if settings.white_list and path not in settings.white_list:
                continue
            if settings.black_list and path in settings.black_list:
                continue

            # Get auth api_keys
            if auth_api_key := settings.auth.get_auth_keys(path):
                headers = {"Authorization": auth_api_key[0]}  # Use the first auth key set
                logger.debug(f"Proxy api({path}) requires auth")
            else:
                headers = None

            for method, body in details.items():
                # Process request parameters
                params: list[tuple[str, Any]] = [
                    (name, c_type)
                    for param in (body.get("parameters") or [])
                    if (name := param.get("name")) and (c_type := type_map.get("type"))
                ]

                # Process request body
                if request_body := body.get("requestBody"):
                    schema_name = (
                        request_body.get("content", {})
                        .get("application/json", {})
                        .get("schema", {})
                        .get("$ref", "")
                        .rsplit("/", 1)[-1]
                    )
                    if not (model_schema := components.get(schema_name)):
                        raise ValueError(f"Schema '{schema_name}' not found in components.")

                    Model = create_pydantic_model(schema_name, model_schema, components)  # noqa
                    params.append(("model", Model))
                logger.opt(colors=True).debug(f"Found proxy api({method}) <y>{url}{path}</y>")
                func_name = body.get("operationId")
                is_stream = path in settings.force_stream_apis
                func = self._create_dynamic_method(
                    func_name, method, params, f"{url}{path}", stream=is_stream, headers=headers
                )
                setattr(self, func_name, func)

                # Register router
                plugin_api = PluginApi(
                    deployment_name=BACKEND_NAME,
                    func_name="register_route",
                )
                handle = adapter.get_handle(PROXY_PLUGIN_NAME)
                await adapter.call_func(
                    plugin_api,
                    path=path,
                    methods=[method],
                    func_name=func_name,
                    params=params,
                    handle=handle,
                    stream=is_stream,
                    direct_output=True,
                    tags=[__plugin_meta__.name],
                )

                # Proxy api to map
                self.func_map[path] = func

    async def __call__(self, proxy_path: str, **kwargs: Any) -> Any:
        if func := self.func_map.get(proxy_path):
            return await func(**kwargs)
        raise RuntimeError(f"api({proxy_path}) not found")

    async def fetch_response(
        self,
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None] | dict | str:
        clent = httpx.AsyncClient(timeout=self.time_out)
        if stream:

            async def stream_generator() -> AsyncGenerator[str, None]:
                async with clent.stream(**kwargs) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        yield chunk

            return stream_generator()

        response = await clent.request(**kwargs)
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
        stream: bool = False,
        headers: dict[str, str] | None = None,
    ) -> Callable[..., Any]:
        # Build a Pydantic request model (for data validation)
        model_name = f"{func_name.title()}_RequestModel"
        RequestModel = create_model(model_name, **{k: (t, ...) for k, t in params})  # type: ignore # noqa

        # Construct dynamic methods
        async def dynamic_method(**kwargs: Any) -> AsyncGenerator[str, None] | dict[str, Any] | str:
            logger.info(f"Calling proxy url: {url} with kwargs: {kwargs}")
            validated = RequestModel(**kwargs)  # Type Validation
            query = {}
            json_body = None
            for field_name, value in validated:
                if isinstance(value, BaseModel):
                    json_body = value.model_dump()
                else:
                    query[field_name] = value
            try:
                return await self.fetch_response(
                    stream=stream,
                    method=method.upper(),
                    url=url,
                    params=query,
                    json=json_body if method.upper() != "GET" else None,
                    headers=headers,
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
