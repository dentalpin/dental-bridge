"""Transform Gesdén ``DCitasPeriod`` rows into :class:`CanonicalAppointmentRecurrence`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.appointment import CanonicalAppointmentRecurrence
from dental_bridge.core.canonical.base import derive_canonical_uuid


def _coerce_int(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalAppointmentRecurrence:
    source_id = str(row["IdCitasP"])
    return CanonicalAppointmentRecurrence(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "appointment_recurrence", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        description=normalise_string(row.get("Texto")),
        starts_on=clean_date(row.get("FechaInicio")),
        ends_on=clean_date(row.get("FechaFinal")),
        weekly_cadence=_coerce_int(row.get("Frecuencia")),
    )
