# Integrating Ray Engine

FrameX supports **multiple execution backends**. To switch to **Ray** for distributed execution, you **don’t need to change any code** — simply turn it on in the configuration.

> **Recommendation:**
>
> - Keep `use_ray = false` during day-to-day development and local debugging.
> - Enable Ray **only in production** (or staging) where distributed execution improves throughput and tail latency.

______________________________________________________________________

## Quick Start

Enable Ray in your `config.toml`:

```toml
[server]
use_ray = true             # ← toggle on Ray
```

No code changes are required. Your existing plugins, @on_request(...) handlers, and cross-plugin calls will continue to work.
FrameX will place plugin deployments on Ray actors and route requests accordingly.

## What’s Ray?

Ray simplifies distributed computing by providing:

- **Scalable compute primitives**: Tasks and actors for painless parallel programming
- **Specialized AI libraries**: Tools for common ML workloads like data processing, model training, hyperparameter tuning, and model serving
- **Unified resource management**: Seamless scaling from laptop to cloud with automatic resource handling

## When to Use Ray

- High concurrency / throughput workloads
- CPU/GPU intensive algorithms
- Horizontal scaling across multiple nodes
- Background or non-blocking long-running tasks (see Distributed Remote Calls)

**Keep it disabled for:**

- Rapid iteration, local debugging, or stepping through code (simpler without Ray)
- Unit testing (use framex.run(test_mode=true))

## Why Ray?

Enabling Ray gives FrameX the ability to:

- 🚀 **Boost performance** with **high concurrency** and **high throughput** distributed computation.
- 🧩 **Isolate blocking plugins** so that if one plugin experiences latency or heavy computation, it won’t block other plugins from responding.
- 📦 **Distribute heavy workloads** (e.g., model inference, batch computation) across multiple nodes, avoiding single-node bottlenecks.
- 🔄 **Offload blocking tasks** to Ray’s distributed task scheduler, preventing API endpoints from hanging and improving responsiveness.
- ⚖️ **Scale elastically** — add more Ray workers to handle increasing workloads without code changes.

This makes Ray especially suitable for **production environments** running large-scale algorithmic systems.
