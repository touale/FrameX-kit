# Plugin Loading & Startup

This chapter explains how FrameX loads plugins and starts the runtime.

## Loading Methods

FrameX supports two loading methods:

1. load plugins in Python code
1. declare plugins in configuration

In both cases, startup ends with `framex.run()`.

## Load Plugins in Python Code

Use `load_builtin_plugins(...)` for built-in plugins and `load_plugins(...)` for your own plugins.

```python
import framex


def main() -> None:
    framex.load_builtin_plugins("echo")
    framex.load_plugins("your_project.plugins.foo")
    framex.run()


if __name__ == "__main__":
    main()
```

### Multiple Plugins

```python
import framex


def main() -> None:
    framex.load_builtin_plugins("echo", "proxy")
    framex.load_plugins(
        "your_project.plugins.foo",
        "your_project.plugins.bar",
    )
    framex.run()
```

### Package Path

You can also load a package path:

```python
framex.load_plugins("your_project.plugins")
```

Use a module path when you want one plugin:

- `your_project.plugins.foo`

Use a package path when you want FrameX to search under that package:

- `your_project.plugins`

Every loaded plugin module or package must define:

```python
__plugin_meta__ = PluginMetadata(...)
```

## Load Plugins from Configuration

You can declare the startup plugin list in `config.toml`:

```toml
load_builtin_plugins = ["echo", "proxy"]
load_plugins = [
  "your_project.plugins.foo",
  "your_project.plugins.bar",
]
```

Then start FrameX normally:

```python
import framex

framex.run()
```

This is useful when different environments need different plugin sets without changing code.

## Load Plugins from CLI

The CLI exposes the same loading model.

```bash
framex run --load-builtin-plugins echo --load-plugins your_project.plugins.foo
```

Both options are repeatable:

```bash
framex run \
  --load-builtin-plugins echo \
  --load-builtin-plugins proxy \
  --load-plugins your_project.plugins.foo \
  --load-plugins your_project.plugins.bar
```

Do not pass them as comma-separated strings.

## Built-In Plugins vs Your Plugins

- `load_builtin_plugins(...)` loads built-in plugins such as `echo` and `proxy`
- `load_plugins(...)` loads your own plugin import paths

Example:

```python
framex.load_builtin_plugins("proxy")
framex.load_plugins("your_project.plugins.foo")
```

## Startup Order

The normal startup sequence is:

1. load built-in plugins if needed
1. load your own plugins
1. call `framex.run()`

If you are using configuration-based loading, `framex.run()` reads the configured plugin lists and starts the runtime.

## Rule of Thumb

Use this simple rule:

- one plugin module: `your_project.plugins.foo`
- multiple plugin modules: repeat `load_plugins(...)`
- one plugin package tree: `your_project.plugins`
- built-in plugin: `load_builtin_plugins(...)`

Keep plugin paths explicit and stable. That makes startup behavior easier to understand and debug.
