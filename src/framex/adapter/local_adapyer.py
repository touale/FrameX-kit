import asyncio
import inspect
import threading
from collections.abc import Callable
from typing import Any

from typing_extensions import override

from framex.adapter.base import AdapterMode, BaseAdapter
from framex.consts import BACKEND_NAME

_lock = threading.Lock()


class LocalAdapter(BaseAdapter):
    mode = AdapterMode.LOCAL

    @override
    def to_deployment(self, cls: type, **kwargs: Any) -> type:
        if tag := kwargs.get("name"):
            setattr(cls, "deployment_name", tag)
        return super().to_deployment(cls, **kwargs)

    @override
    def get_handle(self, deployment_name: str) -> Any:
        from framex.driver.ingress import app

        return (
            app.state.deployments_dict.get(deployment_name) if deployment_name != BACKEND_NAME else app.state.ingress
        )

    @override
    def bind(self, deployment: Callable[..., Any], **kwargs: Any) -> Any:
        return deployment(**kwargs)

    @staticmethod
    def _safe_plot_wrapper(func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Wrap plotting calls with a thread lock to prevent renderer concurrency."""
        with _lock:
            return func(*args, **kwargs)

    @override
    def to_remote_func(self, func: Callable) -> Callable:
        """Wrap a function so it can be used as an async remote function.

        - If `func` is async → directly await it.
        - If `func` is sync → run it in thread pool via asyncio.to_thread().
        - If function name or module suggests matplotlib plotting, lock it to prevent concurrency errors.
        """

        async def _remote_func(*args: tuple[Any, ...], **kwargs: Any) -> Any:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return await asyncio.to_thread(self._safe_plot_wrapper, func, *args, **kwargs)

        func.remote = _remote_func  # type: ignore[attr-defined]
        return func
