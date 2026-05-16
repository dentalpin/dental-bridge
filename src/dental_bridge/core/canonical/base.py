"""Base class and shared utilities for every canonical entity emitted to DPMF."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field

# Project-wide UUIDv5 namespace.
# Stable, deliberately hard-coded so that every adapter (in this repo or
# downstream) derives identical canonical UUIDs for the same source row.
# Changing this constant would re-key every existing DPMF file — never do it
# without a major version bump of both the format and every adapter.
CANONICAL_NAMESPACE_UUID = UUID("dde7d63a-1f43-4ed8-8b91-67b5e9c7c0f7")


def derive_canonical_uuid(source_system: str, entity_type: str, source_id: str) -> UUID:
    """Return the deterministic UUIDv5 for a source row.

    The name fed to UUIDv5 is ``f"{source_system}:{entity_type}:{source_id}"``.
    Including the entity_type guards against collisions when two source tables
    happen to use overlapping primary-key value spaces (e.g. integer IDs that
    start from 1 in every table).
    """
    name = f"{source_system}:{entity_type}:{source_id}"
    return uuid5(CANONICAL_NAMESPACE_UUID, name)


class BaseCanonicalEntity(BaseModel):
    """Provenance envelope carried by every canonical entity."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
    )

    canonical_uuid: UUID = Field(
        description=(
            "Stable identifier across re-extractions. UUIDv5 over "
            "(source_system, entity_type, source_id) under the project namespace."
        )
    )
    source_system: str = Field(
        description="Adapter identifier emitting this entity (e.g. 'gesden')."
    )
    entity_type: str = Field(
        description=(
            "Canonical entity type name (e.g. 'patient'). Lower-snake-case, "
            "matches the DPMF entity table name."
        )
    )
    source_id: str = Field(description="Native primary key from the source system, as a string.")
    adapter_version: str = Field(description="Version of the adapter that produced this entity.")
    extracted_at: datetime = Field(
        description="UTC timestamp at which the entity was read from the source."
    )
    raw_source_data: dict[str, Any] = Field(
        description="Original source row, preserved verbatim for auditability."
    )
