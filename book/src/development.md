# Development Guide

This guide is for contributors who want to work on FrameX locally and keep changes aligned with the current README and book chapters.

## Getting Started

Create a local environment and install the project in editable mode:

```bash
uv sync --dev
```

If you want to verify the runtime quickly, start the built-in echo plugin:

```bash
framex run --load-builtin-plugins echo
```

## Recommended Workflow

1. Make your change in a feature branch.
1. Keep code, examples, and docs consistent with the public API.
1. Run the relevant tests before opening a pull request.
1. Re-run formatting if a hook changes files.

The commands you will use most often are:

```bash
poe test-all
```

## Dependency Management

Use `uv` to manage dependencies:

```bash
uv add requests
uv add pytest --group dev
uv remove requests
uv lock --upgrade-package requests
```

After dependency changes, sync the environment again:

```bash
uv sync --dev
```

## Project Tasks

`poe` exposes the main project tasks:

```bash
poe help
```

Common tasks include:

- `style`: format and fix style issues
- `lint`: run style and type checks
- `test`: run the fast test set
- `test-all`: run the full test suite
- `build`: build source and wheel packages
- `publish`: publish the package to PyPI

## Commit Style

This project uses short, conventional commit messages:

```text
<type>: <message>
```

Common types are `feat`, `fix`, `docs`, `refactor`, `test`, `build`, and `chore`.

Examples:

```text
feat: add plugin config loading example
fix: handle proxy plugin response errors
docs: update quickstart for builtin plugins
```

## Before You Open A PR

Make sure the following are true:

- the code runs locally
- tests pass
- formatting hooks pass
- docs and examples still match the current CLI behavior

Keeping changes small and focused makes review faster and reduces accidental regressions.
