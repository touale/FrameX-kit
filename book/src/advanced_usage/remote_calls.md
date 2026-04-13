# Advanced Remote Calls & Non-Blocking Execution

The `@remote()` decorator has one core role in FrameX: move execution-heavy work behind a separate execution boundary while keeping the call site stable.

## Core Role

A plugin route can be lightweight at the API layer, while the work behind it is not.

That work may involve:

- blocking synchronous libraries
- long-running computation
- legacy code that is not fully async
- logic that should keep the same call form in local mode and Ray mode

If that work stays inline inside the plugin handler, the plugin becomes harder to isolate and harder to move across execution backends later.

Even though enabling **Ray** ensures that one plugin's heavy workload will not block **other plugins**, it does not prevent **blocking inside a single plugin** itself.

If some part of your plugin code performs a blocking operation, such as `time.sleep`, long-running computation, or a non-async library call, the entire plugin instance may become unresponsive.

`@remote()` gives that work a stable execution boundary without changing the surrounding plugin API.

If you are defining a plugin API, use `@on_request(...)`. If you are defining execution work behind that API, use `@remote()`.

## Typical Uses

Use `@remote()` when you want one of these outcomes:

- keep blocking or heavy work out of the main plugin handler path
- keep the same call form in both local mode and Ray mode
- isolate execution-heavy logic without changing the plugin API surface
- prepare code that runs locally today but may run through Ray later

## What This Looks Like

A plugin handler stays focused on request handling:

```python
from framex.plugin import on_request, remote


@remote()
def heavy_job(x: int) -> int:
    return x * 2


@on_request("/api/v1/demo/run")
async def run_job(x: int):
    return await heavy_job.remote(x)
```

That is the main pattern: keep the API-facing handler small, and move execution-heavy work behind `@remote()`.

## Supported Shapes

The current implementation supports:

- plain functions
- instance methods
- class methods

The stable call form is:

```python
await func.remote(...)
```

## Execution Behavior

The same `.remote(...)` call uses different execution paths depending on the active adapter.

In local mode:

- async functions are awaited directly
- sync functions run through `asyncio.to_thread(...)`

In Ray mode:

- the callable is wrapped through `ray.remote(...)`
- `.remote(...)` executes through Ray

That is the key point: the call interface stays stable while the backend changes.

Ray backend setup is covered in [Integrating Ray Engine](./ray_engine.md).

## More Examples

### Plain Function

```python
from framex.plugin import remote


@remote()
def heavy_job(x: int) -> int:
    return x * 2


result = await heavy_job.remote(21)
```

### Instance Method

```python
from framex.plugin import remote


class Worker:
    @remote()
    def total(self, values: list[int]) -> int:
        return sum(values)


count = await Worker().total.remote([1, 2, 3])
```

### Class Method

```python
from framex.plugin import remote


class Worker:
    @classmethod
    @remote()
    def scale(cls, x: int) -> int:
        return x * 10


value = await Worker.scale.remote(2)
```

## Rule Of Thumb

Use `@remote()` when you need one callable interface with backend-dependent execution.

Use `@on_request(...)` for APIs. Use `@remote()` for the work those APIs call behind the scenes.
