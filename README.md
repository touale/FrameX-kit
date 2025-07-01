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
class RequestModel(BaseModel):
    message: str
    id: str


@on_register()
class MyPlugin(BasePlugin):
    def __init__(self, remote_apis: dict[str, PluginApi]):
        super().__init__(remote_apis)

    @on_request(call_type=ApiType.FUNC)
    async def __call__(self, data: dict):
        return {"echo": data}

    @on_request("/health", methods=["GET"], call_type=ApiType.HTTP)
    async def health_check(self):
        return {"status": "ok"}

    @on_request("/call_remote_plugin", methods=["POST"])
    async def health_check(self, model: MyBaseModel):
        return await self._call_remote_api(
            "echo:Deployment:__call__",
            model=RequestModel(message="hello", id="1").model_dump(),
        )
```
