# Plugin Configuration

FrameX configuration has two layers:

1. runtime configuration for the whole service
1. plugin-specific configuration under `plugins.<plugin_name>`

This chapter focuses on the settings you are most likely to use in real projects.

## Where Configuration Comes From

FrameX loads settings from these sources:

- environment variables
- `.env`
- `.env.prod`
- `config.toml`
- `[tool.framex]` in `pyproject.toml`

In the current implementation, environment variables take highest priority. `config.toml` and `[tool.framex]` are useful project-level defaults.

CLI options are then applied before startup, so flags such as `--port`, `--load-plugins`, and `--load-builtin-plugins` can override configuration at runtime.

## Minimal `config.toml`

For most projects, `config.toml` is the clearest place to start.

Example:

```toml
load_builtin_plugins = ["echo"]
load_plugins = ["your_project.plugins.foo"]

[server]
host = "127.0.0.1"
port = 8080
use_ray = false
enable_proxy = false

[plugins.foo]
debug = true
```

The most common top-level fields are:

- `load_builtin_plugins`
- `load_plugins`
- `server`
- `plugins`
- `auth`

## Most Common Runtime Settings

In normal usage, the most important settings are:

- `server.host`
- `server.port`
- `server.use_ray`
- `server.enable_proxy`
- `load_builtin_plugins`
- `load_plugins`
- `plugins.<plugin_name>`
- `auth.rules`

You do not need to understand every field in the global `Settings` model before using FrameX productively. Most projects only touch a small subset.

## Plugin-Specific Configuration

Plugin-specific settings live under:

```toml
[plugins.<plugin_name>]
```

Example:

```toml
[plugins.foo]
debug = true
timeout = 30
```

This keeps plugin settings separate from global runtime settings.

## Typed Plugin Configuration

If a plugin wants typed configuration, it can declare a Pydantic model and attach it through `config_class` in `PluginMetadata`.

### Define a config model

```python
from pydantic import BaseModel


class FooConfig(BaseModel):
    debug: bool = False
    timeout: int = 30
```

### Attach it to plugin metadata

```python
__plugin_meta__ = PluginMetadata(
    name="foo",
    version=VERSION,
    description="A minimal example plugin",
    author="you",
    url="https://github.com/touale/FrameX-kit",
    required_remote_apis=[],
    config_class=FooConfig,
)
```

### Read it inside the plugin

```python
from framex.plugin import get_plugin_config

settings = get_plugin_config("foo", FooConfig)
```

If no config is provided for that plugin, FrameX returns the config model with its default values and logs a warning.

## Example: Plugin Config in `config.toml`

If the plugin is named `foo`, the matching config block looks like this:

```toml
[plugins.foo]
debug = true
timeout = 30
```

That block is what `get_plugin_config("foo", FooConfig)` reads.

## Environment Variables

Nested settings can also be provided through environment variables with `__` as the separator.

Examples:

```bash
export SERVER__PORT=9000
export SERVER__ENABLE_PROXY=true
export PLUGINS__FOO__DEBUG=true
```

Because the current settings model uses `case_sensitive=False`, you do not need to rely on lowercase-only keys.

## When to Use Which Format

Use `config.toml` when:

- you want readable project defaults
- the configuration is hierarchical
- you want plugin settings grouped clearly in version control

Use environment variables when:

- deployment environments need different overrides
- secrets or environment-specific values should not live in the repo
- CI, containers, or runtime platforms inject settings dynamically

A practical pattern is:

- keep stable defaults in `config.toml`
- use environment variables for deployment-specific overrides

## Rule of Thumb

Keep this mental model:

- `server.*` configures the runtime
- `load_plugins` and `load_builtin_plugins` control what gets loaded
- `plugins.<plugin_name>` configures one plugin
- `config_class` + `get_plugin_config(...)` gives that plugin typed settings

That is enough for most real FrameX projects.
