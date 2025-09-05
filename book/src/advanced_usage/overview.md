# Advanced Usage

This section covers **advanced features of FrameX** that go beyond the basic plugin lifecycle.\
While the basic usage allows you to register, configure, and run plugins easily, advanced usage focuses on **scalability, compatibility, and resilience** in production systems.

______________________________________________________________________

## Topics

- **[System Proxy Plugin (v2 API Compatibility)](./system_proxy_plugin.md)**\
  Learn how to use the built-in **proxy plugin** to forward requests to legacy v2 APIs.\
  This ensures **smooth migration** from v2 to v3 without breaking compatibility, and provides a zero-code-change transition once an algorithm is upgraded.

- **[Integrating Ray Engine](./ray_engine.md)**\
  Switch the execution backend to **Ray** with a single configuration change.\
  Gain **distributed execution**, **high concurrency**, and **fault isolation**, ideal for production workloads.

- **[Advanced Remote Calls & Non-Blocking Execution](./remote_calls.md)**\
  Mark blocking functions with `@remote` to offload them into **distributed, non-blocking execution**.\
  Prevent plugin-level blocking while keeping your code simple and async-friendly.

- **[Monitoring & Tracing](./monitor.md)**\
  Integrate with **Sentry** to capture errors, monitor performance, and trace requests across plugins.\
  Provides full observability for both development and production environments.

______________________________________________________________________

## Why Advanced Usage Matters?

- 🔄 **Compatibility**: Seamlessly migrate from v2 APIs.
- ⚡ **Performance**: Handle large-scale workloads with Ray.
- 🛡️ **Resilience**: Avoid blocking with distributed remote calls.
- 📊 **Observability**: Gain insights into runtime behavior with tracing and monitoring.

These features are optional for development but **essential for production** environments where scalability and stability are critical.
