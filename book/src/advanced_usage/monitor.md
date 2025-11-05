# Monitoring & Tracing

FrameX integrates both Sentry and Ray Dashboard for comprehensive monitoring and tracing.
This enables you to capture errors, exceptions, performance metrics, task status, and distributed resource usage across the entire system with minimal setup.

**Benefits**

- ✅ Automatic error capturing (no manual try/except needed).
- ✅ Performance tracing (slow APIs, blocked tasks, async bottlenecks).
- ✅ Centralized monitoring across multiple plugins.
- ✅ Distributed resource and task monitoring via Ray Dashboard.
- ✅ Flexible configuration per environment.

______________________________________________________________________

## 1) Quick Setup

### Sentry Configuration

Simply add a `[sentry]` section to your configuration file (config.toml):

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

### Ray Dashboard Configuration

To enable distributed monitoring, configure the [server] section:

```
[server]
dashboard_host = "127.0.0.1"
dashboard_port = 8260
use_ray=true
```

Once Ray is running, the dashboard is available at:

```
http://127.0.0.1:8260
```

Note that you need to switch the engine to Ray.
