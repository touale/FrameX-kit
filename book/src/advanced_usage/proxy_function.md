# Proxy Function & Remote Invocation

This chapter introduces the **proxy function mechanism** in FrameX, including a new decorator, runtime support, and an HTTP endpoint for **remote proxy invocation**.

This feature enables **cross-FrameX-instance function execution**, allowing plugins to transparently call functions hosted on remote FrameX instances.

______________________________________________________________________

## 1) Background & Motivation

In multi-FrameX deployments, different instances may run under different security or infrastructure constraints.

Typical scenarios include:

- Instance A does not have access to MySQL
- Instance A is restricted to HTTP-only outbound access
- Instance B has database access or privileged network permissions

To fully implement plugin functionality without violating security constraints, FrameX introduces the **on_proxy mechanism**, enabling remote function proxying across FrameX instances.

______________________________________________________________________

## 2) Design Overview

- Functions can be marked as proxy-enabled
- FrameX automatically decides whether to execute locally or remotely
- No explicit client/server role configuration is required
- The same code runs on both sides

______________________________________________________________________

## 3) Defining a Proxy Function

### Step 1: Register Proxy Function in Plugin

Proxy functions must be registered during plugin startup.

> **Important:** Lazy import is required.

```python
@on_register()
class ExamplePlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    async def on_start(self) -> None:
        from demo.some import example_func  # Important: Lazy import

        register_proxy_func(example_func)
```

______________________________________________________________________

### Step 2: Mark Function with on_proxy

```python
@on_proxy()
@other_func
async def example_func(id, user):
    data = "..."
    return data
```

______________________________________________________________________

## 4) Enabling Remote Proxy Invocation

To enable remote execution, add the following configuration to `config.toml`.

### Proxy Configuration

```toml
[plugins.proxy]
proxy_urls = ["http://remotehost:8080"]
white_list = ["/api/v1/proxy/remote"]
proxy_functions = {
  "http://localhost:8083" = [
    "demo.some.example_func"
  ]
}
```

### Authentication Configuration

```toml
[plugins.proxy.auth]
general_auth_keys = ["7a23713f-c85f-48c0-a349-7a3363f2d30c"]
auth_urls = ["/api/v1/proxy/remote"]
```

Once configured, FrameX automatically routes function calls to remote instances when required.

______________________________________________________________________

## 5) Security, Performance & Compatibility

### Security

- Automatic serialization and deserialization
- Data compression and encryption
- Safe fallback when local decorators fail

### Compatibility

Supports:

- Primitive types
- BaseModel (Pydantic)
- Most stateless class objects
