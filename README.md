# FrameX

**FrameX** (short for **Framework Extension**) is a lightweight, pluggable plugin injection framework for Python. It provides a clean and extensible architecture to build modular applications — where each component can be registered, isolated, and invoked dynamically.

FrameX is ideal for systems that need runtime extensibility, plugin composition, or distributed function routing.

______________________________________________________________________

## ✨ Features

- 🧩 **Plugin-as-a-Service**
  Register classes or methods as callable services with simple decorators.

- 🔌 **Hot-pluggable Architecture**
  Load, register, or unload plugins dynamically.

- 🧷 **Dependency & Permission Declaration**
  Plugins can declare required dependencies and permissions, which are validated before use.

- ⚡ **Ray Serve Native Support**
  Built-in support for Ray deployment handles and high-concurrency distributed inference.

- 🧪 **Test-friendly by Design**
  Easy to mock, trace, and validate plugin behaviors in isolation.

______________________________________________________________________

## 🚀 Quick Example

```python
# src/plugin_demo/plugins/my_plugin/__init__.py
from pydantic import BaseModel

from framex import PluginMetadata, logger, on_register, BasePlugin, PluginApi
from framex.plugin.model import ApiType
from framex.plugin.on import on_request

__plugin_meta__ = PluginMetadata(
    name="yuan shen plugin",
    version="1.0",
    description="my_plugin description",
    author="yuan shen zhen hao wan",
    url="https://github.com/yuan shen",
    required_remote_apis=["echo:Deployment:__call__", "/api/v1/get_version"],
)


class RequestModel(BaseModel):
    message: str
    id: str


@on_register(num_replicas=1)
class MyPlugin(BasePlugin):
    def __init__(self, remote_apis: dict[str, PluginApi]):
        super().__init__(remote_apis)

    @on_request(
        call_type=ApiType.FUNC
    )  # Expose your own remote function for others to call
    async def __call__(self, data: dict):
        return {"echo": data}

    @on_request(
        "/health",
        methods=["GET", "POST"],
        call_type=ApiType.HTTP,  # Expose your own remote http api and function for others to call
    )
    async def health_check(self):
        return {"status": "ok"}

    @on_request("/call_remote_plugin", methods=["POST"])
    async def health_check(self, model: MyBaseModel):
        return await self._call_remote_api(  # Call other people's plugins
            "echo:Deployment:__call__",
            model=model,
        )

    ...
```

```python
# src/plugin_demo/main.py

import framex

framex.load_plugins("src/plugin_demo/plugins")
framex.run()
```
