# Plugin Configuration

FrameX supports **TOML**, **YAML**, and **ENV** (including `.env`) configuration formats and allows **nested Pydantic models** for strongly-typed settings.

We **recommend TOML** for multi-level configuration, as it is cleanly hierarchical and scales well when new plugin options are added.

## 1) System Config (Overview)

The runtime loads a top-level `Settings` model that typically includes:

- `server: ServerConfig` — host/port, dashboard, `use_ray`, `enable_proxy`
- `log: LogConfig` — log formatting and prefixes to ignore
- `sentry: SentryConfig` — Sentry toggles, DSN, env (`local|dev|prod`), lifecycle
- `test: TestConfig` — test switches
- `plugins: dict[str, Any]` — plugin-specific raw config
- `load_builtin_plugins: list[str]` — which **built-in** plugins to load (e.g. `"proxy"`)
- `load_plugins: list[str]` — which **third-party** plugins to load
- `data_dir: Path` — per-plugin persistent data/config directory (default: `data/`)

The only configurations you need to focus on are server, load_plugins, load_builtin_plugins, and plugins. FrameX automatically manages everything else.

### Example

By default, the runtime reads from **`config.toml`** at the project root.
**`config.toml`**

```toml
# Load built-in and third-party plugins
load_builtin_plugins = ["proxy", "echo"]
load_plugins = ["your plugin"]

[server]
use_ray = false
enable_proxy = false
host = "127.0.0.1"
port = 8080
```

## 2) Plugin Config (typed)

Each plugin can define a dedicated typed config model and have it injected automatically at registration time.

### 1. Define a config model

```
class ProxyPluginConfig(BaseModel):
    proxy_urls: list[str] = []
    force_stream_apis: list[str] = []
    black_list: list[str] = []
    white_list: list[str] = []
```

### 2. Get it by `get_plugin_config`

```
from framex.plugin import get_plugin_config
settings = get_plugin_config({PLUGIN_NAME}, ProxyPluginConfig)
```

## 3) Where to Put Plugin Config

There are two supported locations. Choose one per plugin:

### Plan A) (Recommended) Inline in the root config.toml

Add a sub-table under [plugins.\<plugin_name>] in `config.toml`:

```
load_builtin_plugins = ["proxy"]

[server]
use_ray = false
enable_proxy = true

[plugins.proxy]
proxy_urls = ["http://127.0.0.1:8080"]
force_stream_apis = ["/api/v1/chat"]
```

### Plan B) Dedicated file under the data directory

Each plugin can have an isolated config file under:

```
./data/<plugin_name>/config.toml
```

For example: add it easily in `data/proxy/config.toml`:

```
proxy_urls = ["http://127.0.0.1:8080"]
force_stream_apis = ["/api/v1/chat"]
```

When you start the plugin, it will automatically create the directory. You can view the directory location in the `def __init__(..,data_dir:str,...)`stage.

## 4) Supported Formats & Loading Order

Supported sources (from highest to lowest precedence):

1. **ENV settings** (process environment variables)
1. **dotenv** file (e.g., `.env`)
1. `data/<plugin>/config.toml` (plugin-level TOML config)
1. `data/<plugin>/config.yaml` / `config.yml` (plugin-level YAML config)
1. Project root `config.toml` (global TOML)
1. Project root `config.yaml` / `config.yml` (global YAML)
1. `pyproject.toml` (project-level fallback)

> **Recommendation:** Prefer **TOML** for hierarchical configuration. It is expressive, diff-friendly, and scales well as plugins evolve.
