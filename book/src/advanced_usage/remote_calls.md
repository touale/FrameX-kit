# Advanced Remote Calls & Non-Blocking Execution

Even though enabling **Ray** ensures that one plugin’s heavy workload will not block **other plugins**, it does not prevent **blocking inside a single plugin** itself.

If some part of your plugin code performs a blocking operation (e.g., `time.sleep`, long-running computation, or a non-async library call), the entire plugin instance may become unresponsive.

FrameX provides the `@remote` decorator to solve this issue:

- it offloads the decorated function to **distributed execution** (via Ray when enabled, or a fallback mechanism otherwise), making it **non-blocking** by design.

______________________________________________________________________

## How It Works

- Add `@remote()` to a method (sync or async).
- Call it with `.remote(...)` instead of normal invocation.
- FrameX automatically executes the method in a separate worker (via Ray when available).
- Your plugin remains responsive, even if the method blocks.

## Example Highlights

**Blocking sync code**

```python
@remote()
def remote_sleep():
    time.sleep(0.1)
    return "remote_sleep"
```

**Async functions supported**

```
@remote()
async def remote_func_async_with_params(a: int, b: str):
    return f"{a}, {b}"
```

**Inside an API handler**

```
results = [
    await remote_sleep.remote(),
    await remote_func_with_params.remote("123"),
]
```

## Key Benefits

- ✅ Prevents plugin self-blocking.
- ✅ Works with both sync and async methods.
- ✅ Transparent: no code changes needed when Ray is disabled/enabled.
- ✅ Simple syntax: .remote(...) for non-blocking execution.

With @remote, you can safely use blocking libraries, legacy synchronous code, or heavy computations inside FrameX plugins, while still keeping your APIs responsive and scalable.
