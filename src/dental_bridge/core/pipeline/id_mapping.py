"""Mapping between source-system identifiers and canonical UUIDs.

Sprint 1: in-memory only. The runner constructs a single registry per
extraction run. Sprint 2+ will persist this in the SQLite checkpoint store
so a re-run can resume without rebuilding the map.
"""

from __future__ import annotations

from typing import Final
from uuid import UUID

from dental_bridge.core.canonical.base import derive_canonical_uuid

_SOURCE_ID_MAX_REPR: Final[int] = 128


class IdMapping:
    """Resolve foreign keys between canonical entities.

    A foreign-key column on the source side is just a value from another
    table's primary key. To produce the canonical UUID of the referenced
    row, we either:

    1. Re-derive it with :func:`derive_canonical_uuid` — works for any row
       we *would* emit, because UUIDv5 is deterministic. This is the default
       path.
    2. Read it from this registry — needed when the extractor wants to
       confirm that the referenced row actually exists in the extraction
       scope before emitting the FK. The runner ``register``\\ s every
       emitted row.
    """

    def __init__(self) -> None:
        self._map: dict[tuple[str, str, str], UUID] = {}

    def register(self, source_system: str, entity_type: str, source_id: object) -> UUID:
        """Register an emitted row and return its canonical UUID.

        The same (system, entity_type, source_id) triple always yields the
        same UUID; calling ``register`` a second time is a no-op.
        """
        key = self._key(source_system, entity_type, source_id)
        existing = self._map.get(key)
        if existing is not None:
            return existing
        canonical = derive_canonical_uuid(source_system, entity_type, key[2])
        self._map[key] = canonical
        return canonical

    def resolve(
        self,
        source_system: str,
        entity_type: str,
        source_id: object | None,
        *,
        require_known: bool = False,
    ) -> UUID | None:
        """Return the canonical UUID of a referenced row, or ``None``.

        Pass ``require_known=True`` to make the call return ``None`` for any
        source_id that has not been registered yet. With the default
        (``False``), the UUID is derived deterministically even when the
        referenced row is outside the current extraction scope. Use
        ``require_known`` when an unresolved FK should be treated as a
        warning rather than a stable pointer.
        """
        if source_id is None or source_id == "":
            return None
        key = self._key(source_system, entity_type, source_id)
        if require_known:
            return self._map.get(key)
        canonical = self._map.get(key)
        if canonical is not None:
            return canonical
        return derive_canonical_uuid(source_system, entity_type, key[2])

    def __contains__(self, item: tuple[str, str, object]) -> bool:
        system, entity_type, source_id = item
        return self._key(system, entity_type, source_id) in self._map

    def __len__(self) -> int:
        return len(self._map)

    @staticmethod
    def _key(source_system: str, entity_type: str, source_id: object) -> tuple[str, str, str]:
        as_str = str(source_id)
        if len(as_str) > _SOURCE_ID_MAX_REPR:
            # Defensive: a 1MB source_id is almost certainly a bug upstream.
            raise ValueError(f"source_id for ({source_system}, {entity_type}) is implausibly long")
        return source_system, entity_type, as_str
