# Concurrency & Ingress Configuration

This chapter explains where ingress and concurrency settings are configured in FrameX.

The important part is that FrameX has more than one config path, and they do not all affect the same deployment.

## What To Configure

In the current codebase, ingress-related settings are configured in three places:

- `base_ingress_config`
- `server.ingress_config`
- plugin-level kwargs passed to `@on_register(...)`

These settings are forwarded through the adapter layer.

In practice, the most common field is `max_ongoing_requests`.

## `base_ingress_config`: Global Default

`base_ingress_config` is the global default used when FrameX builds deployments.

```toml
base_ingress_config = { max_ongoing_requests = 10 }
```

This value is the starting point for both:

- the main API ingress
- plugin deployments

## `server.ingress_config`: Main API Ingress Override

`server.ingress_config` applies only to the main `APIIngress` deployment.

If you leave it empty, FrameX now computes a default automatically from the number of loaded HTTP deployments.

The current rule is:

- start from `base_ingress_config.max_ongoing_requests`
- multiply it by the number of loaded HTTP deployments
- keep a floor of `base * 6`

So with:

```toml
base_ingress_config = { max_ongoing_requests = 10 }
```

and about 30 loaded plugin deployments, the main API ingress default becomes `300`.

If you want to override that behavior explicitly, set `server.ingress_config` yourself:

```toml
[server]
ingress_config = { max_ongoing_requests = 120 }
```

That explicit value wins over the adaptive default.

## Plugin Ingress Settings

If a plugin needs its own ingress settings, pass them directly into `@on_register(...)`.

```python
from framex.plugin import BasePlugin, on_register


@on_register(max_ongoing_requests=20)
class MyPlugin(BasePlugin):
    pass
```

The built-in `proxy` plugin uses exactly this pattern, but its values come from plugin config:

```toml
[plugins.proxy]
ingress_config = { max_ongoing_requests = 60 }
```

And then inside the plugin:

```python
@on_register(**settings.ingress_config)
class ProxyPlugin(BasePlugin): ...
```

So if you want per-plugin concurrency control, configure it at the plugin level.

## Using It With Ray

If you run FrameX with `server.use_ray = true`, ingress settings become worth tuning.

This is the mode where values like `max_ongoing_requests` matter most for the main API ingress and for plugin deployments.

A practical starting point is:

- leave `server.ingress_config` empty and let FrameX size the main API ingress automatically
- only add plugin-level ingress settings for plugins that are clearly hotter or heavier than the rest
- adjust `num_cpus` separately if the whole Ray runtime needs more CPU capacity

```toml
[server]
use_ray = true
num_cpus = 4
```

If you are still developing locally and not pushing concurrency yet, you usually do not need to tune these values first.

## Using It In Local Mode

In local development, keep this simple.

Start with the defaults, and only add ingress settings after you have a concrete reason such as a hot plugin or a busy Ray deployment target later.

For most local debugging and feature work, these settings are not the first thing to optimize.

## Rule Of Thumb

Use `base_ingress_config` for global defaults.

Leave `server.ingress_config` empty if you want FrameX to size the main API ingress automatically.

Set `server.ingress_config` explicitly when you want a fixed ingress limit for the whole service.

Use plugin-level `@on_register(...)` kwargs, or plugin config forwarded into `@on_register(...)`, when one plugin needs different ingress behavior from the rest of the service.
