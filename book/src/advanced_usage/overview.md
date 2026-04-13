# Advanced Usage

This section covers the parts of FrameX that matter once basic plugin registration is already working.

Use it when your service needs upstream API integration, distributed execution, tighter access control, or more operational tuning than the basic usage section provides.

## Topics

- [Proxy Mode](./system_proxy_plugin.md)
  Bridge upstream HTTP services into the same FrameX surface with the built-in `proxy` plugin.

- [Integrating Ray Engine](./ray_engine.md)
  Run plugin deployments with Ray Serve when you need distributed execution.

- [Advanced Remote Calls & Non-Blocking Execution](./remote_calls.md)
  Use `@remote()` for portable local or Ray-backed remote calls.

- [Security & Authorization](./authentication.md)
  Control access to routes, docs, and APIs with FrameX authentication rules.

- [Concurrency & Ingress Configuration](./concurrency_and_ingress.md)
  Tune ingress and execution behavior for higher traffic or lower latency requirements.

- [Proxy Function & Remote Invocation](./proxy_function.md)
  Use function-style proxying and remote invocation in the plugin model.

- [Simulating Network Communication (For Tests)](./advanced_test.md)
  Test network-facing behavior without depending on real remote services.

- [Monitoring & Tracing](./monitor.md)
  Add observability so request paths and plugin execution are easier to debug.

## When To Read This Section

- after you can register and load basic plugins
- when plugins need to call each other through stable interfaces
- when upstream HTTP services should look like part of the same application
- when local execution is no longer enough and you want to move selected workloads to Ray
- when the service is growing and needs clearer operational boundaries

If you are still learning the basic runtime model, finish the basic usage section first.
