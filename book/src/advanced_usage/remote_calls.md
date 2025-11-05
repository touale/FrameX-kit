# Advanced Remote Calls & Non-Blocking Execution

Even though enabling **Ray** ensures that one plugin’s heavy workload will not block **other plugins**, it does not prevent **blocking inside a single plugin** itself.

If some part of your plugin code performs a blocking operation (e.g., `time.sleep`, long-running computation, or a non-async library call), the entire plugin instance may become unresponsive.

FrameX provides the `@remote` decorator to solve this issue:

- it offloads the decorated function to **distributed execution** (via Ray when enabled, or a fallback mechanism otherwise), making it **non-blocking** by design.

______________________________________________________________________

## 1) How It Works

- Add `@remote()` to a method (sync or async).
- Call it with `.remote(...)` instead of normal invocation.
- FrameX automatically executes the method in a separate worker (via Ray when available).
- Your plugin remains responsive, even if the method blocks.

## 2) Supported Function Types

The @remote decorator is fully compatible with:

- Regular (synchronous) functions
- Asynchronous (async) functions
- Instance methods (with self)
- Static methods and class methods

## 3) Example Highlights

### 1. Add `@remote()` to a method.

(a). Blocking synchronous function

```python
@remote()
def remote_sleep():
    time.sleep(0.1)
    return "remote_sleep"
```

(b). Asynchronous function

```python
@remote()
async def remote_func_async_with_params(a: int, b: str):
    return f"{a}, {b}"
```

(c). Class instance method

```python
class Worker:
    @remote()
    def heavy_compute(self, n: int):
        return sum(i * i for i in range(n))
```

(d). Static method

```python
class Utils:
    @remote()
    @staticmethod
    def convert(data: str) -> str:
        time.sleep(1)
        return data.upper()
```

### 2. Call it with `.remote(...)` instead of normal invocation.

```
results = [
    await remote_sleep.remote(),
    await remote_func_async_with_params.remote(123, "abc"),
    await Worker().heavy_compute.remote(10000),
    await Utils.convert.remote("framex"),
]
```

## 3) Key Benefits

- ✅ Prevents plugin self-blocking.
- ✅ Works with both sync and async methods.
- ✅ Transparent: **no code changes needed when Ray is disabled/enabled.**
- ✅ Simple syntax: .remote(...) for non-blocking execution.

With @remote, you can safely use blocking libraries, legacy synchronous code, or heavy computations inside FrameX plugins, while still keeping your APIs responsive and scalable.
