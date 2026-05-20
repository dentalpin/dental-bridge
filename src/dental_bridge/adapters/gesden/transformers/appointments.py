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

# Mapping from Gesdén's ``IdSitC`` numeric status codes (TSitCita) to
# the coarse canonical taxonomy. Validated against the live ``TSitCita``
# catalog in SOURCE_DB:
#
#   0  Planificada       → SCHEDULED
#   1  Anulada           → CANCELLED
#   2  Recepción         → CONFIRMED (patient arrived, awaiting consult)
#   3  Sala Espera       → CONFIRMED
#   4  Consulta          → ATTENDED  (in the chair)
#   5  Finalizada        → ATTENDED  (treatment done, by far the most common)
#   6  Fallada           → NO_SHOW
#   7  Confirmada        → CONFIRMED
#   8  Encuesta          → ATTENDED  (post-visit survey state)
#   9  Enviado           → CONFIRMED (appointment reminder sent)
#   10 Anulada WhatsApp  → CANCELLED
#
# The full ``status_uuid`` pointing at the catalog entry is still
# emitted alongside ``coarse_status`` so destinations that want the
# original code can fish it out.
_DEFAULT_STATUS_MAP: dict[int, AppointmentStatus] = {
    0: AppointmentStatus.SCHEDULED,
    1: AppointmentStatus.CANCELLED,
    2: AppointmentStatus.CONFIRMED,
    3: AppointmentStatus.CONFIRMED,
    4: AppointmentStatus.ATTENDED,
    5: AppointmentStatus.ATTENDED,
    6: AppointmentStatus.NO_SHOW,
    7: AppointmentStatus.CONFIRMED,
    8: AppointmentStatus.ATTENDED,
    9: AppointmentStatus.CONFIRMED,
    10: AppointmentStatus.CANCELLED,
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


def _resolve_professional_from_usuagd(ctx: TransformContext, id_usu: object | None):
    """Resolve to the TUsuAgd-keyed professional canonical UUID.

    Mirrors the keying convention used by ``extractors/professionals.py``
    when it unions TUsuAgd entries: ``source_id = f"usuagd:{IdUsu}"``.
    """
    if id_usu in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, "professional", f"usuagd:{id_usu}")


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
        # Gesdén's appointment owner is `DCitas.IdUsu` (a TUsuAgd FK),
        # not `IdCol` — the latter is only populated when a *second*
        # collaborator is attached, which clinics rarely use. We point
        # at the TUsuAgd-derived professional UUID (``usuagd:<IdUsu>``)
        # so the importer can resolve a real professional for ~100% of
        # appointments instead of the ~3% covered by IdCol alone.
        professional_uuid=_resolve_professional_from_usuagd(ctx, row.get("IdUsu")),
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
