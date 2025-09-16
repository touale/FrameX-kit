# FAQ & Troubleshooting

## 1. Virtual environment not auto-activated after `uv sync --dev`

**Issue**:\
After running `uv sync --dev`, the virtual environment (`.venv`) is created but not automatically activated.

**Solution**:\
Manually activate the environment:

```bash
source .venv/bin/activate
```

## 2. mypy reports missing type stubs for third-party libraries

```
$ poe lint
Poe => ruff check . --fix
All checks passed!
Poe => mypy .
src/find_policy/__init__.py:7: error: Skipping analyzing "xxxxxx": module is installed, but missing library stubs or py.typed marker  [import-untyped]
src/find_policy/__init__.py:7: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
Found 1 error in 1 file (checked 12 source files)
Error: Sequence aborted after failed subtask '_lint'
```

### Solutions:

(1). (Not recommended) Tell mypy to ignore missing stubs by adding to `mypy.ini` or pyproject.toml:

For example `mindforge`:

```
[mypy-mindforge.*]
ignore_missing_imports = True
```

(2). (Recommended) Install the corresponding type stub package if available.

For example `pytz` `pyyaml`:

```
uv add types-pytz --dev     # for pytz
uv add types-pyyaml --dev   # for pyyaml
```
