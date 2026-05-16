"""Transform Gesdén ``DCitas`` rows into :class:`CanonicalAppointment`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dental_bridge.adapters.gesden.decoders.gesden_date import decode_gesden_date
from dental_bridge.adapters.gesden.decoders.gesden_time import (
    decode_gesden_duration_seconds_to_minutes,
    decode_gesden_time,
)
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.core.canonical.appointment import (
    AppointmentStatus,
    CanonicalAppointment,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid

# Best-effort mapping from Gesdén's ``IdSitC`` numeric status codes to the
# coarse canonical taxonomy. The actual semantics are defined in the
# clinic's TSitCita table — that's why the full status_uuid (pointing at
# the catalog entry) is always emitted too. This map only powers the
# convenience ``coarse_status`` field.
_DEFAULT_STATUS_MAP: dict[int, AppointmentStatus] = {
    1: AppointmentStatus.SCHEDULED,
    2: AppointmentStatus.CONFIRMED,
    3: AppointmentStatus.ATTENDED,
    4: AppointmentStatus.NO_SHOW,
    5: AppointmentStatus.CANCELLED,
}


def _decode_status(value: object | None) -> AppointmentStatus:
    if value is None or value == "":
        return AppointmentStatus.UNKNOWN
    try:
        return _DEFAULT_STATUS_MAP.get(int(value), AppointmentStatus.UNKNOWN)
    except (TypeError, ValueError):
        return AppointmentStatus.UNKNOWN


def _coerce_int(value: object | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_datetime(value: object | None) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _resolve_catalog(ctx: TransformContext, kind: str, source_id: object | None):
    if source_id in (None, "", 0):
        return None
    return derive_canonical_uuid(ctx.source_system, "catalog_item", f"{kind}:{source_id}")


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalAppointment:
    # Composite source_id — DCitas' real PK is (IdUsu, IdOrden), not IdCita.
    source_id = f"{row['IdUsu']}:{row['IdOrden']}"

    return CanonicalAppointment(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "appointment", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        chair_uuid=_resolve_catalog(ctx, "chair", row.get("IdBox")),
        status_uuid=_resolve_catalog(ctx, "appointment_status", row.get("IdSitC")),
        recurrence_uuid=_resolve(ctx, "appointment_recurrence", row.get("IdCitasP")),
        scheduled_date=decode_gesden_date(row.get("Fecha")),
        scheduled_time=decode_gesden_time(row.get("Hora")),
        duration_minutes=decode_gesden_duration_seconds_to_minutes(row.get("Duracion")),
        notes=normalise_string(row.get("Texto")),
        coarse_status=_decode_status(row.get("IdSitC")),
        created_at=_coerce_datetime(row.get("FecAlta")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
