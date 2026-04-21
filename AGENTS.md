# Repository Guidelines

## Project Structure & Module Organization

Core code lives under `src/framex/`. Key packages include `driver/` for FastAPI app wiring and auth, `plugin/` for plugin loading and registration, `plugins/` for built-in plugins, `repository/` for GitHub/GitLab release and access checks, and `utils/` for shared docs/config helpers. Demo code is under `src/A_demo/`. Tests mirror the code layout in `tests/`, with focused areas such as `tests/api/`, `tests/driver/`, `tests/adapter/`, and plugin fixtures in `tests/plugins/`.

## Architecture Notes

`framex.run()` is the main assembly entrypoint. It loads plugins, builds deployment handles, derives HTTP plugin APIs, and then starts either local FastAPI mode or Ray Serve mode. Treat this as the runtime composition root.

Be rigorous and conservative when changing architecture-sensitive code:

- Make the smallest change that fixes the issue.
- Do not introduce new abstractions, public models, or configuration unless the existing boundary cannot support the fix.
- Before editing, identify the exact state layer involved: load-time plugin registry, runtime ingress state, adapter/Ray handles, request auth context, or docs rendering.
- Avoid speculative rewrites. If a design is uncertain, pause and clarify instead of iterating through multiple incompatible implementations.
- Keep token ownership explicit. Never pass a user token to a repository provider unless the provider is known to match the user's OAuth provider.

The plugin system has a strict split between load-time state and runtime state:

- Load-time plugin registration lives in `framex.plugin.manage._manager._plugins` and is populated by the custom import hook (`PluginFinder` / `PluginLoader`) when plugin modules are imported.
- Runtime serving mainly uses `deployments`, `PluginApi` metadata, `app.state.deployments_dict`, and Ray Serve handles.
- In local mode, these often appear to be the same world because everything stays in one process.
- In Ray mode, they are not interchangeable. A route or deployment can work even when `_manager._plugins` is not the right source of truth for that execution context.

Do not "fix" Ray issues by re-running `auto_load_plugins()` or trying to reload plugins inside worker setup. Plugin loading is not designed as a repeatable synchronization mechanism, and repeating it can corrupt plugin-manager state such as duplicate plugin IDs or install/load tracking.

When debugging Ray-specific behavior, first decide which state layer the failing code actually needs:

- If the code needs request-serving data, prefer runtime sources such as `PluginApi`, ingress state, deployment names, or Ray handles.
- If the code needs plugin metadata only for docs or display, verify whether that metadata is already serialized into runtime structures before reaching for `get_plugin()`.
- Only use `get_plugin()` when the current execution context is guaranteed to share the original plugin load-time registry.

### Implementation & Design Style

Keep feature work boundary-first and explicit:

- Put public or user-facing configuration in `framex.config` with narrow typed fields. Prefer explicit `Literal` options over free-form strings when values affect behavior, styling, transport, or security.
- Keep view-model shaping near the rendering layer. Do not put UI serialization helpers or presentation-only transformations in `driver/application.py`; that module should assemble routes and runtime behavior.
- Keep browser-visible data minimal. Treat rendered HTML and JavaScript as visible to any authenticated docs user, and never serialize secrets, internal URLs, tokens, headers, or fixed request payloads unless the feature explicitly requires public disclosure.
- Keep server-only behavior on the server. If a UI action needs sensitive configuration, have the browser call an internal FrameX endpoint and let the server apply private URL, headers, auth, query, JSON body, or form body.
- Make ownership of user inputs explicit. Model where an input lands instead of guessing from names; for example, use explicit targets such as query params versus request body fields.
- Prefer small, composable helpers at the correct layer over ad hoc inline logic. A helper is justified when it protects a boundary, removes repeated serialization logic, or makes security constraints obvious.

For UI design, prefer restrained, predictable controls over arbitrary styling:

- Use preset variants for visual intent, such as default, primary, success, warning, and danger. Avoid per-instance arbitrary CSS unless the project has an established design-token path for it.
- Preserve existing layout rhythm, spacing, and button styling before introducing new visual language.
- If a control triggers a remote action, show a clear pending state and a clear success/error result. Do not leave users guessing whether a click did anything.
- For user input, provide labels, placeholders, defaults, and required-state behavior where applicable.

Test boundary behavior directly: server route behavior in `tests/driver/`, rendering and sanitized view-model behavior in `tests/test_utils.py`, and API-facing behavior in `tests/api/`. Use fake HTTP clients in tests; do not call real internal services or include real tokens.

## Build, Test, and Development Commands

Use `uv` and Poe tasks.

- `uv sync` — install project dependencies.
- `uv run framex` — run the app locally with the current environment.
- `uv run poe test` — run the test suite (`pytest tests`).
- `uv run poe lint` — run Ruff fixes plus MyPy checks.
- `uv run poe style` — format code with Ruff and apply safe auto-fixes.
- `uv run poe build` — build source and wheel packages.

For targeted work, prefer commands like `.venv/bin/pytest tests/api/test_proxy.py -k plugin_config`.

## Coding Style & Naming Conventions

Use 4-space indentation, type hints on functions and methods, and English for comments and technical docs. Keep functions short and direct. Prefer explicit names over abbreviations. Follow current APIs, e.g. `model_dump()` for Pydantic models. Use `ruff format` and `ruff check` for formatting and linting, and `mypy` for type validation. Module names use `snake_case`; classes use `PascalCase`; tests use `test_*.py` and `test_*` function names.

## Testing Guidelines

Pytest is the test runner, with `pytest-asyncio`, `pytest-cov`, `pytest-order`, and `pytest-recording` enabled. Add tests next to the affected area: API behavior in `tests/api/`, auth and app wiring in `tests/driver/`, and repository/provider logic in `tests/test_utils.py` or `tests/test_config.py`. Keep fixtures sanitized; do not use real internal hosts, project names, or secrets in tests.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commits such as `feat: ...` and `docs: ...`. Keep commit subjects short and imperative. PRs should describe the behavior change, note any config or auth impact, and include the exact test commands run. Add screenshots only when `/docs` or UI-facing output changes.

## Security & Configuration Tips

Do not expose real tokens, internal URLs, or business identifiers in code or tests. `/docs/plugin-config` is sensitive by design: keep auth checks enforced, mask secrets in rendered config, and restrict embedded file reads to the workspace plus whitelist rules.
