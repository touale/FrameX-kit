import inspect
import json
from collections.abc import AsyncGenerator, Callable
from typing import Any, cast

import httpx
from pydantic import BaseModel, create_model

from framex.consts import APP_NAME, BACKEND_NAME, PROXY_PLUGIN_NAME, VERSION
from framex.log import logger
from framex.plugin import BasePlugin, PluginApi, PluginMetadata, call_remote_api, on_register
from framex.plugin.model import ApiType
from framex.plugin.on import on_request
from framex.plugins.proxy.builder import create_pydantic_model, type_map
from framex.plugins.proxy.config import ProxyPluginConfig

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


@on_register()
class ProxyPlugin(BasePlugin):
    def __init__(self, config: ProxyPluginConfig, **kwargs: Any) -> None:
        self.config = config
        self._client = httpx.AsyncClient(timeout=600)

        self.func_map: dict[str, Any] = {}

        super().__init__(**kwargs)

    async def on_start(self) -> None:
        if not self.config.proxy_urls:
            logger.warning("No url provided, skipping proxy plugin")
            return
        for url in self.config.proxy_urls:
            await self._parse_openai_docs(url)
        logger.success(f"Succeeded to parse openai docs form {url}")

    @on_request(call_type=ApiType.FUNC)
    async def check_is_gen_api(self, path: str) -> bool:
        return path in self.config.force_stream_apis

    async def _get_openai_docs(self, url: str) -> dict[str, Any]:
        response = await self._client.get(f"{url}/api/v1/openapi.json")
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def _parse_openai_docs(self, url: str) -> None:
        openapi_data = await self._get_openai_docs(url)
        paths = openapi_data.get("paths", {})
        components = openapi_data.get("components", {}).get("schemas", {})

        for path, details in paths.items():
            for method, body in details.items():
                if parameters := body.get("parameters"):
                    params = [
                        (name, c_type)
                        for param in parameters
                        if (name := param.get("name")) and (c_type := type_map.get("type"))
                    ]
                else:
                    params = []

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
                is_stream = path in self.config.force_stream_apis
                func = self._create_dynamic_method(func_name, method, params, f"{url}{path}", stream=is_stream)
                setattr(self, func_name, func)

                # Register router
                plugin_api = PluginApi(
                    deployment_name=BACKEND_NAME,
                    func_name="register_route",
                )
                from ray import serve

                handle = serve.get_deployment_handle(PROXY_PLUGIN_NAME, app_name=APP_NAME)
                await call_remote_api(
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
        if api := self.func_map.get(proxy_path):
            return await api(**kwargs)
        raise RuntimeError(f"api({proxy_path}) not found")

    async def fetch_response(
        self,
        stream: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None] | dict | str:
        if stream:

            async def stream_generator() -> AsyncGenerator[str, None]:
                async with self._client.stream(**kwargs) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        yield chunk

            return stream_generator()

        response = await self._client.request(**kwargs)

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
    ) -> Callable[..., Any]:
        # Build a Pydantic request model (for data validation)
        model_name = f"{func_name.title()}_RequestModel"
        RequestModel = create_model(model_name, **{k: (t, ...) for k, t in params})  # type: ignore # noqa

        # Construct dynamic methods
        async def dynamic_method(**kwargs: Any) -> AsyncGenerator[str, None] | dict[str, Any] | str:
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
