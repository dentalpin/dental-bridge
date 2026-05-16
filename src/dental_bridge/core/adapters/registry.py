"""Discovery of installed origin adapters via Python entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dental_bridge.core.adapters.origin_abc import OriginAdapter

_ENTRY_POINT_GROUP = "dental_bridge.adapters"


def discover() -> dict[str, type[OriginAdapter]]:
    """Return a mapping of adapter name → class for every adapter currently installed."""
    found: dict[str, type[OriginAdapter]] = {}
    for ep in entry_points(group=_ENTRY_POINT_GROUP):
        found[ep.name] = ep.load()
    return found
