import inspect

import httpx
from pydantic import BaseModel, create_model

from framex.consts import APP_NAME, BACKEND_NAME, VERSION
from framex.log import logger
from framex.plugin import BasePlugin, PluginApi, PluginMetadata, call_remote_api, on_register
from framex.plugins.proxy.builder import type_map
from plugin_demo.plugins.aaa.t import build_pydantic_model

__plugin_meta__ = PluginMetadata(
    name="proxy",
    version=VERSION,
    description="一个特殊的 framx proxy 插件, 充当透明代理。它接收 API 请求并将其转发到已配置的外部 HTTP 端点,并将响应返回给调用者。",
    author="touale",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
)


@on_register()
class ProxyPlugin(BasePlugin):
    def __init__(self, remote_apis: dict[str, PluginApi]):
        self.urls = ["http://172.22.121.63:31617"]
        self._client = httpx.AsyncClient(timeout=600)

        super().__init__(remote_apis)

    async def on_start(self):
        for url in self.urls:
            await self._parse_openai_docs(url)
        logger.success(f"Succeeded to parse openai docs form {url}")

    async def _get_openai_docs(self, url):
        response = await self._client.get(f"{url}/api/v1/openapi.json")
        response.raise_for_status()
        return response.json()

    async def _parse_openai_docs(self, url: str):
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

                    Model = build_pydantic_model(schema_name, model_schema, components)  # noqa
                    params.append(("request", Model))

                logger.opt(colors=True).debug(f"Found proxy api({method}) <y>{path}</y>, params: {params}")

                func_name = body.get("operationId")
                func = self._create_dynamic_method(func_name, method, params, f"{url}{path}")
                setattr(self, func_name, func)

                plugin_api = PluginApi(
                    deployment_name=BACKEND_NAME,
                    func_name="register_route",
                )
                from ray import serve

                handle = serve.get_deployment_handle("proxy:ProxyPlugin", app_name=APP_NAME)
                await call_remote_api(
                    plugin_api,
                    path=path,
                    methods=[method],
                    func_name=func_name,
                    params=params,
                    handle=handle,
                    direct_output=True,
                )

    def _create_dynamic_method(
        self,
        func_name: str,
        method: str,
        params: list[tuple[str, type]],
        proxy_url: str,
    ):
        # Build a Pydantic request model (for data validation)
        model_name = f"{func_name.title()}_RequestModel"
        RequestModel = create_model(model_name, **{k: (t, ...) for k, t in params})  # type: ignore # noqa

        # Construct dynamic methods
        async def dynamic_method(**kwargs):
            validated = RequestModel(**kwargs)  # Type Validation

            query = {}
            json_body = None
            for field_name, value in validated:
                if isinstance(value, BaseModel):
                    json_body = value.model_dump()
                else:
                    query[field_name] = value

            try:
                response = await self._client.request(
                    method=method.upper(),
                    url=proxy_url,
                    params=query,
                    json=json_body if method.upper() != "GET" else None,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.opt(exception=e, colors=True).error(
                    f"Error calling proxy api({method}) <y>{proxy_url}</y>: {e}"
                )
                return "error proxy"

        # Construct a signature and set all parameters as required
        sig = inspect.Signature(
            [
                inspect.Parameter(k, inspect.Parameter.KEYWORD_ONLY, annotation=t, default=inspect.Parameter.empty)
                for k, t in params
            ]
        )
        dynamic_method.__signature__ = sig  # type: ignore
        dynamic_method.__annotations__ = {k: t for k, t in params}
        dynamic_method.__name__ = func_name

        return dynamic_method
