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

## Key Directories and Files

- src/ – Main source code directory.
  - __main__.py: **Application entry point.**
  - consts.py: Constants (e.g., version).
  - log.py: Logging setup.
  - plugins/: **All plugins must be placed here.**
- tests/ – Unit and integration tests.
- pyproject.toml – Project configuration and dependency management.
- ruff.toml / mypy.ini – Linting and type-checking configuration.
- data/ – Sample or runtime data.
- poe_tasks.toml – Task automation configuration.
- releaserc.toml – Release configuration.

## Plugin Directory

All FrameX plugins must live inside the plugins/ directory.
You can structure them in two ways:

### 1. Single-file plugin

Each .py file inside plugins/ is treated as one plugin.
Example:

```
src/demo_project/plugins/
├── __init__.py
└── demo.py     # defines one plugin
```

### 2. Folder-based plugin

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

## Guidelines

- Every plugin must be placed under plugins/.
- Each plugin should have a clear entry point (__init__.py or main class).
- Use single-file plugins for simple functionality.
- Use folder-based plugins for more complex features requiring multiple modules.
