from framex.adapter.base import BaseAdapter
from framex.adapter.local_adapter import LocalAdapter
from framex.config import settings

_adapter: BaseAdapter | None = None


def get_adapter() -> BaseAdapter:
    global _adapter
    if _adapter is None:
        if settings.server.use_ray:
            from framex.adapter.ray_adapter import RayAdapter

            _adapter = RayAdapter()
        else:
            _adapter = LocalAdapter()
    return _adapter
