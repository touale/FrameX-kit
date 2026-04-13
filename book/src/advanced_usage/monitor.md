# Monitoring & Tracing

FrameX supports two practical monitoring paths today: Sentry for application errors and traces, and Ray Dashboard for distributed execution visibility.

## Sentry

Sentry is enabled through the `sentry` config block.

```toml
[sentry]
enable = true
dsn = "<your-sentry-dsn>"
env = "local"
debug = true
ignore_errors = []
lifecycle = "trace"
enable_logs = true
```

## What Sentry Covers

- application errors and exceptions
- trace collection when `lifecycle = "trace"`
- optional log capture with `enable_logs = true`
- custom ignore rules through `ignore_errors`

FrameX only initializes Sentry when `enable`, `dsn`, and `env` are all set.

## Ray Dashboard

Ray Dashboard is available when the service runs with `use_ray = true`.

```toml
[server]
use_ray = true
dashboard_host = "127.0.0.1"
dashboard_port = 8260
```

When Ray starts, the dashboard is available at the configured host and port.

## Log Noise Control

FrameX also keeps routine logs readable through the `log` and `server` config blocks.

```toml
[log]
simple_log = true
ignored_contains = ["GET /ping", "GET /health"]

[server]
excluded_log_paths = ["/api/v1/openapi.json"]
```

This helps keep health checks, docs traffic, and Ray noise out of the main request logs.

## Notes

- Sentry environment names are combined with the adapter mode internally, so local and Ray runs are separated.
- The OpenAPI page includes a small runtime status block with uptime and version information.
- FrameX does not currently ship a separate metrics backend beyond Sentry and Ray Dashboard.
