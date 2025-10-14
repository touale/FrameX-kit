import asyncio

from pydantic import BaseModel, ConfigDict

from framex import remote

# ============================================================
# Test Fixtures
# ============================================================


class ExampleClass:
    """Test target: normal class with instance, async, and class methods."""

    @remote()
    def sync_instance_method(self, a: int, b: int) -> str:
        """Simulate a synchronous instance method decorated with @remote."""
        import time

        time.sleep(0.01)
        return f"sync_instance_method:{a},{b}"

    @remote()
    async def async_instance_method(self, a: int, b: int) -> str:
        """Simulate an asynchronous instance method decorated with @remote."""
        await asyncio.sleep(0.01)
        return f"async_instance_method:{a},{b}"

    @remote()
    @classmethod
    def sync_class_method(cls, a: int, b: int) -> str:
        """Simulate a synchronous class method decorated with @remote."""
        import time

        time.sleep(0.01)
        return f"{cls.__name__}.sync_class_method:{a},{b}"


@remote()
def sync_function(a: int, b: int) -> str:
    """Test target: synchronous function decorated with @remote."""
    import time

    time.sleep(0.01)
    return f"sync_function:{a},{b}"


@remote()
async def async_function(a: int, b: int) -> str:
    """Test target: asynchronous function decorated with @remote."""
    await asyncio.sleep(0.01)
    return f"async_function:{a},{b}"


class ExampleModel(BaseModel):
    """Test target: Pydantic model with a classmethod using @remote."""

    model_config = ConfigDict(ignored_types=(object,))
    a: str
    b: str

    @remote()
    @classmethod
    def sync_class_method(cls, a: int, b: int) -> str:
        """Simulate a classmethod inside a Pydantic model decorated with @remote."""
        import time

        time.sleep(0.01)
        return f"{cls.__name__}.sync_class_method:{a},{b}"


# ============================================================
# Unit Tests
# ============================================================


async def test_remote_sync_instance_method():
    """Verify that a sync instance method works with @remote()."""
    obj = ExampleClass()
    result = await obj.sync_instance_method.remote(1, 2)
    assert result == "sync_instance_method:1,2"


async def test_remote_async_instance_method():
    """Verify that an async instance method works with @remote()."""
    obj = ExampleClass()
    result = await obj.async_instance_method.remote(3, 4)
    assert result == "async_instance_method:3,4"


async def test_remote_sync_class_method():
    """Verify that a classmethod works with @remote()."""
    result = await ExampleClass.sync_class_method.remote(5, 6)
    assert result == "ExampleClass.sync_class_method:5,6"


async def test_remote_pydantic_class_method():
    """Verify that a Pydantic model classmethod works with @remote()."""
    result = await ExampleModel.sync_class_method.remote(7, 8)
    assert result == "ExampleModel.sync_class_method:7,8"


async def test_remote_sync_function():
    """Verify that a module-level sync function works with @remote()."""
    result = await sync_function.remote(9, 10)
    assert result == "sync_function:9,10"


async def test_remote_async_function():
    """Verify that a module-level async function works with @remote()."""
    result = await async_function.remote(11, 12)
    assert result == "async_function:11,12"
