from framex.adapter.base import BaseAdapter
from framex.adapter.local_adapyer import LocalAdapter
from framex.adapter.ray_adapter import RayAdapter
from framex.config import settings

_adapter: BaseAdapter | None = None


def get_adapter() -> BaseAdapter:
    global _adapter
    if _adapter is None:
        _adapter = RayAdapter() if settings.server.use_ray else LocalAdapter()
    return _adapter
