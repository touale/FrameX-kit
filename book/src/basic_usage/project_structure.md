# Project Structure

In practice, FrameX projects usually fall into **two different structures**.

You should choose the structure based on what you are publishing and how many plugins the project contains.

## Structure 1: Single Plugin Package

Use this structure when the project itself is **one plugin package**.

This is a good fit when you want to:

- build one reusable plugin
- publish it to PyPI
- let other FrameX projects load it directly by import path

Recommended layout:

```text
your_plugin/
├── pyproject.toml
├── README.md
├── src/
│   └── your_plugin/
│       ├── __init__.py
│       ├── config.py
│       ├── models.py
│       └── service.py
└── tests/
```

In this structure, the plugin entry is usually defined in:

```text
src/your_plugin/__init__.py
```

That means other projects can load it directly, for example:

```bash
framex run --load-plugins your_plugin
```

Or in `config.toml`:

```toml
load_plugins = ["your_plugin"]
```

### When to use it

Choose this structure when:

- the package contains one plugin
- the plugin is intended to be reused across projects
- you want the package name itself to be the plugin import path

### Why it works

Because the whole package is the plugin, using `src/your_plugin/__init__.py` as the plugin entry is natural here.

The package is small, self-contained, and meant to be loaded as one unit.

## Structure 2: Multi-Plugin Project

Use this structure when one project contains **multiple plugins**.

This is a good fit when you want to:

- build several capabilities in one service
- let different people or teams own different plugins
- load only part of the project in different environments

Recommended layout:

```text
your_project/
├── pyproject.toml
├── config.toml
├── README.md
├── src/
│   └── your_project/
│       ├── __init__.py
│       ├── __main__.py
│       ├── consts.py
│       └── plugins/
│           ├── __init__.py
│           ├── foo.py
│           └── bar/
│               ├── __init__.py
│               ├── config.py
│               └── service.py
└── tests/
```

In this structure, plugins usually live under:

```text
src/your_project/plugins/
```

Typical import paths are:

- `your_project.plugins.foo`
- `your_project.plugins.bar`

Examples:

```bash
framex run --load-plugins your_project.plugins.foo
```

```toml
load_plugins = [
  "your_project.plugins.foo",
  "your_project.plugins.bar",
]
```

### When to use it

Choose this structure when:

- one project contains multiple plugins
- different capabilities should stay clearly separated
- you want cleaner ownership boundaries inside one codebase

### Why it works

Because the project package and the plugin modules are different things.

- `your_project` is the application package
- `your_project.plugins.*` are the plugin packages or modules

That separation makes the codebase easier to understand and maintain.

## Single File vs Package Plugin

Inside a multi-plugin project, each plugin can still be organized in two ways.

### Single-file plugin

```text
src/your_project/plugins/
└── foo.py
```

Use this when the plugin is still small.

### Package plugin

```text
src/your_project/plugins/
└── bar/
    ├── __init__.py
    ├── config.py
    ├── models.py
    └── service.py
```

Use this when the plugin is larger and needs multiple modules.

## Built-In Plugins vs Your Plugins

Keep built-in plugins and your own plugins separate.

- built-in plugins come from `framex.plugins`, such as `echo` and `proxy`
- your own plugins come from your own package

Example:

```bash
framex run \
  --load-builtin-plugins echo \
  --load-plugins your_project.plugins.foo
```

## Rule of Thumb

Use this simple rule:

- if the package itself is one reusable plugin, put the plugin in `src/your_plugin/__init__.py`
- if the project contains multiple plugins, create `src/your_project/plugins/`
- if one plugin grows large, turn it from one file into one package
