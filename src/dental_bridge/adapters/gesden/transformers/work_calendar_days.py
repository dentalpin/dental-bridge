"""Transform Gesdén ``TCalDias`` rows into :class:`CanonicalWorkCalendarDay`.

``TCalDias`` does not carry a per-date override — the real schema is
``(IdCal, IdDia, IdUsu, IdSit)`` associating a user and a situation
with each weekday of a calendar. We emit one canonical row per source
row, encoding the composite key as ``IdCal:IdDia:IdUsu`` so the UUID
is deterministic.

``CanonicalWorkCalendarDay.day`` is left ``None`` because there is no
calendar-date to attach — ``IdDia`` is the weekday number. The full
source payload remains in ``raw_source_data`` for importers that need
to reconstruct the per-weekday-per-user-per-situation matrix.
"""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.work_calendar import CanonicalWorkCalendarDay


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalWorkCalendarDay:
    composite = f"{row['IdCal']}:{row['IdDia']}:{row.get('IdUsu') or 0}"
    calendar_uuid = derive_canonical_uuid(ctx.source_system, "work_calendar", str(row["IdCal"]))

    return CanonicalWorkCalendarDay(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "work_calendar_day", composite),
        source_system=ctx.source_system,
        source_id=composite,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        calendar_uuid=calendar_uuid,
        day=None,
        is_working_day=None,
        notes=None,
    )
