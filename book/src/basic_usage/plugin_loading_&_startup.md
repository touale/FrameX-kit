# Plugin Loading & Startup

FrameX supports two ways to load plugins:

1. **Programmatically** (in code)
1. **Declaratively** via **configuration** (`config.toml` or other supported formats)

Both approaches end with starting the runtime using `framex.run()`.

______________________________________________________________________

## 1) Programmatic Loading

Import `framex` in your application entrypoint and load plugins explicitly.

```python
def main() -> None:
    import framex

    # 1) Load built-in plugins (shipped with FrameX)
    framex.load_builtin_plugins("echo")  # system/built-in plugin

    # 2) Load a single plugin (module or package)
    # framex.load_plugins("your_project.plugins.plugin_name")
    # ✅ Example:
    # framex.load_plugins("demo_project.plugins.hello_world")

    # 3) Load multiple plugins at once
    # framex.load_plugins("xxx.plugin_a", "xxx.plugin_b")
    # ✅ Example:
    # framex.load_plugins(
    #     "demo_project.plugins.hello_world",
    #     "demo_project.plugins.play_games",
    # )

    # 4) Load an entire plugins package (recommended)
    #    This recursively discovers all valid plugins under the `plugins/` directory.
    #    Every discovered module/package must define `__plugin_meta__`.
    # framex.load_plugins("your_project.plugins")
    # framex.load_plugins("your_project")

    # Finally, start the runtime
    framex.run()
```

Notes:

- Each discovered module/package must declare __plugin_meta__ = PluginMetadata(...).

## 2) Configuration-Based Loading

You can specify which plugins to load from your config (e.g., config.toml). This is the simplest way to manage environments and deployments.

```
# Built-in plugins (shipped with FrameX)
load_builtin_plugins = ["proxy"]

# Third-party or app plugins (python import paths)
load_plugins = ["someone.plugins"]
```

At startup, FrameX reads the config (see Plugin Configuration section for formats and precedence), automatically loads the declared plugins, and then starts the service with framex.run().

What these fields mean

- load_builtin_plugins — a list of built-in (platform) plugins to enable (e.g., "proxy").
- load_plugins — a list of user/application plugin import paths:
- Single module plugin: "demo_project.plugins.hello_world"
- Package plugin (folder): "demo_project.plugins"
- Multiple entries allowed.

______________________________________________________________________

## 3) Discovery Rules & Requirements

- Metadata: Every plugin module/package must define __plugin_meta__ = PluginMetadata(...).
- Layout: Both single-file (plugins/foo.py) and folder-based plugins (plugins/bar/) are supported.
- Errors: If a plugin fails validation, FrameX will log a clear error and skip it.
