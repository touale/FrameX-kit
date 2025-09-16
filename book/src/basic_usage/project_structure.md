# Project Structure

A typical project generated with **FrameX** follows a standardized structure to ensure consistency, maintainability, and easy plugin management.

```bash
$ tree demo_project
demo_project
|-- LICENSE
|-- README.md
|-- data
|   `-- demo@f738
|-- mypy.ini
|-- poe_tasks.toml
|-- pyproject.toml
|-- releaserc.toml
|-- ruff.toml
|-- src
|   `-- demo_project
|       |-- __init__.py
|       |-- __main__.py
|       |-- consts.py
|       |-- log.py
|       `-- plugins
|           |-- __init__.py
|           `-- demo.py
|-- tests
|   |-- __init__.py
|   `-- test_add.py
`-- uv.lock
```

______________________________________________________________________

## 1) Key Directories and Files

- src/ – Main source code directory.
  - __main__.py: **Application entry point.**
  - consts.py: Constants (e.g., version).
  - log.py: Logging setup.
  - plugins/: **All plugins can be placed here.**
- tests/ – Unit and integration tests.
- pyproject.toml – Project configuration and dependency management.
- ruff.toml / mypy.ini – Linting and type-checking configuration.
- data/ – Sample or runtime data.
- poe_tasks.toml – Task automation configuration.
- releaserc.toml – Release configuration.
- __init__.py - **Single plugin can be placed here.**

## 2) Where should the plugin be placed

> The difference from **Single plugin management** is that one is placed in `src/demo_project/__init__.py`, and **Multiple plugin management** is in `src/demo_project/plugins/`!

### Single plugin

If there is only one algorithm or only one plugin, you can directly prevent its entry in the package's __init__.py.

Example:

```
src/demo_project/
├── __init__.py # defines one plugin
```

### Multiple plugin

All FrameX plugins can live inside the plugins/ directory.
You can structure them in two ways:

### A. Easy-file plugin

Each .py file inside plugins/ is treated as one plugin.
Example:

```
src/demo_project/plugins/
├── __init__.py
└── demo.py     # defines one plugin
```

### B. Folder-based plugin

A plugin can also be organized as a package (folder). This is recommended for more complex plugins with multiple modules.
Example:

```
$ tree ../src/framex/plugins -I '__pycache__|*.pyc|*.pyo|*.pyd'
../src/framex/plugins
├── __init__.py
├── echo.py          # single-file plugin
└── proxy/           # folder-based plugin
    ├── __init__.py
    ├── builder.py
    └── config.py
```

Here, two plugins are defined:

- echo – a simple single-file plugin (echo.py)
- proxy – a more complex plugin implemented as a package with multiple modules

______________________________________________________________________

## 3) Guidelines

- Every plugin must be placed under plugins/.
- Each plugin should have a clear entry point (__init__.py or main class).
- Use single-file plugins for simple functionality.
- Use folder-based plugins for more complex features requiring multiple modules.
