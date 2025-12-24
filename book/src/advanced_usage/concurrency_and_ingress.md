# Concurrency & Ingress Configuration

This chapter introduces how to configure **concurrency, scaling, and ingress behavior** in FrameX using **Ray**.\
By tuning these parameters, you can control instance count, request concurrency, and overall throughput.

______________________________________________________________________

## 1) Overview

FrameX supports additional **Ray Serve ingress configurations** to improve:

- Maximum concurrent requests
- Request queueing behavior
- Instance-level load control

These configurations are applied through `ingress_config` and can be defined at different levels with clear inheritance rules.

This chapter uses `max_ongoing_requests` as an example.

______________________________________________________________________

## 2) Base Ingress Configuration

FrameX provides a global base configuration:

```toml
base_ingress_config = {"max_ongoing_requests" = 10}
```

**Behavior**

- Acts as the **default ingress configuration**
- Automatically inherited by:
  - Server
  - All plugins
- Can be overridden at lower levels

______________________________________________________________________

## 3) Server-Level Ingress Configuration

You can override the base configuration at the **server level**:

```toml
[server]
ingress_config = {"max_ongoing_requests" = 60}
```

**Behavior**

- Applies to server-level ingress
- Overrides `base_ingress_config`

______________________________________________________________________

## 4) Plugin-Level Ingress Configuration

Plugins can define their own ingress configuration.

Example for the **proxy plugin**:

```toml
[plugins.proxy]
ingress_config = {"max_ongoing_requests" = 60}
```

### Behavior

- Takes precedence over both:
  - `server.ingress_config`
  - `base_ingress_config`
- Only applies to the specific plugin

______________________________________________________________________

## 5) Plugin Development: Custom Ingress Configuration

If a plugin requires a custom `max_ongoing_requests` or other Ray Serve parameters, follow these steps.

### 1. Add ingress_config to Plugin Config

```python
from pydantic import BaseModel
from typing import Any


class ExamplePluginConfig(BaseModel):
    ingress_config: dict[str, Any] = {"max_ongoing_requests": 60}
```

______________________________________________________________________

### 2. Apply ingress_config During Registration

Use the `on_register` decorator to inject ingress parameters:

```python
@on_register(**settings.ingress_config)
class ExamplePlugin(BasePlugin):
    def __init__(self, **kwargs: Any) -> None: ...
```

### Behavior

- `settings.ingress_config` is passed directly to Ray Serve
- Allows fine-grained control per plugin
- Fully compatible with Ray Serve autoscaling and concurrency features

______________________________________________________________________

## 6) Configuration Inheritance Rules

Ingress configuration follows a **top-down inheritance model**:

1. `base_ingress_config`
1. `plugins.<plugin_name>.ingress_config`

If a plugin does not define `ingress_config`, it automatically inherits from the nearest parent level.

**Complete Example: config.toml**

```toml
base_ingress_config = {"max_ongoing_requests" = 10}

[server]
ingress_config = {"max_ongoing_requests" = 60}

[plugins.proxy]
ingress_config = {"max_ongoing_requests" = 60}
```

______________________________________________________________________

## 7) Supported Ray Serve Parameters

In addition to `max_ongoing_requests`, Ray Serve supports many advanced parameters such as:

- Autoscaling behavior
- Replica scaling limits
- Request queue management

For the complete and up-to-date list, refer to the official Ray Serve documentation:

https://docs.rayai.org.cn/en/latest/serve/advanced-guides/advanced-autoscaling.html
