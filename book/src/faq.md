# FAQ & Troubleshooting

## `uv sync --dev` created `.venv`, but the shell is not activated

`uv sync` installs the environment, but it does not automatically source it.

Activate it manually:

```bash
source .venv/bin/activate
```

## `framex run` starts, but my plugin is not loaded

Make sure you pass the correct load option.

Use `--load-builtin-plugins` for built-in plugins, or `--load-plugins` for your own plugin packages. Both options can be repeated.

```bash
framex run --load-builtin-plugins echo
framex run --load-plugins my_plugin --load-plugins another_plugin
```

## `pre-commit.ci` reports `files were modified by this hook`

That means the hook reformatted files in CI.

Run the same formatter locally, commit the updated files, and push again:

```bash
pre-commit run --all-files
```

If the repo uses `pre-commit.ci`, the auto-fix only applies to writable pull request branches. It does not create a new pull request for you.

## `mypy` complains about missing stubs

This usually means a third-party dependency does not ship type information.

There are two practical solutions.

### Solution 1: Ignore That Dependency In Mypy

This is not the recommended option, but it is acceptable when no stub package exists.

Add a targeted ignore rule in `mypy.ini` or `pyproject.toml`.

For example, for `mindforge`:

```ini
[mypy-mindforge.*]
ignore_missing_imports = True
```

Avoid disabling missing-import checks globally. Keep the ignore rule scoped to the specific dependency.

### Solution 2: Install The Stub Package

This is the recommended option when a matching type stub package exists.

For example:

```bash
uv add types-pytz --dev
uv add types-pyyaml --dev
```

Use this path for libraries such as:

- `pytz` -> `types-pytz`
- `pyyaml` -> `types-pyyaml`

If a stub package exists, prefer installing it over adding an ignore rule.
