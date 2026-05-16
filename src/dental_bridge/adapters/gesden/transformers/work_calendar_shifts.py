"""Transform Gesdén ``TCalHor`` rows into :class:`CanonicalWorkCalendarShift`.

``TCalHor`` has a composite key ``(IdCal, IdDia, HIni)``: weekday + start
of the shift uniquely identify the band. ``HIni``/``HFin`` are encoded
in minutes-since-midnight, ``IdDia`` is the weekday number 1..7.
"""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.gesden_time import (
    decode_gesden_time,  # seconds-since-midnight
)
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.work_calendar import CanonicalWorkCalendarShift


def _decode_weekday(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return None
    if 1 <= as_int <= 7:
        return as_int
    return None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalWorkCalendarShift:
    composite = f"{row['IdCal']}:{row['IdDia']}:{row.get('HIni') or 0}"
    calendar_uuid = derive_canonical_uuid(ctx.source_system, "work_calendar", str(row["IdCal"]))

    return CanonicalWorkCalendarShift(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "work_calendar_shift", composite),
        source_system=ctx.source_system,
        source_id=composite,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        calendar_uuid=calendar_uuid,
        weekday=_decode_weekday(row.get("IdDia")),
        start_time=decode_gesden_time(row.get("HIni")),
        end_time=decode_gesden_time(row.get("HFin")),
    )
