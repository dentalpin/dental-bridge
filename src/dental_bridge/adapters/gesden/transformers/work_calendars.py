"""Transform Gesdén ``TCalCa`` rows into :class:`CanonicalWorkCalendar`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.work_calendar import CanonicalWorkCalendar


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalWorkCalendar:
    source_id = str(row["IdCal"])

    center_uuid = None
    if row.get("IdCentro") not in (None, "", 0, -1):
        center_uuid = derive_canonical_uuid(ctx.source_system, "center", str(row["IdCentro"]))

    return CanonicalWorkCalendar(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "work_calendar", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        code=None,  # TCalCa carries no short code column.
        name=normalise_string(row.get("Descripcio")),
        center_uuid=center_uuid,
        chair_uuid=None,  # Calendar is not scoped to a chair in this schema.
        valid_from=None,
        valid_until=None,
    )
