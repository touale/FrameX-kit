# Monitoring & Tracing

FrameX integrates **Sentry** for monitoring and tracing.\
This allows you to capture **errors, exceptions, performance bottlenecks, and logs** automatically with minimal setup.

**Benefits**

- ✅ Automatic error capturing (no manual try/except needed).
- ✅ Performance tracing (slow APIs, blocked tasks).
- ✅ Centralized monitoring across multiple plugins.
- ✅ Flexible configuration per environment.

______________________________________________________________________

## 1) Quick Setup

Simply add a `[sentry]` section to your configuration file:

```toml
[sentry]
enable = true
dsn = "<your-sentry-dsn>"
env = "local"        # e.g., local, dev, prod
debug = true
ignore_errors = []
lifecycle = "trace"
integration = []
enable_logs = true
```

- enable: Toggles Sentry integration on/off.
- dsn: Your Sentry DSN (Data Source Name).
- env: Environment tag for grouping events (e.g. local, dev, prod).
- debug: Prints debug logs for Sentry itself.
- ignore_errors: A list of errors to ignore.
- lifecycle: Mode of event tracking (manual or trace).
- enable_logs: Captures logs in addition to errors.

## 2) Internal Sentry Service

We also maintain an internal **Sentry instance**.
In our development and production environments, monitoring and tracing are already enabled.

If you need to connect your plugin or project to the internal Sentry, please request the DSN key from your system administrator.
