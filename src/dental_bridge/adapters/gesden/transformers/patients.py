"""Transform a Gesdén ``Pacientes`` row into :class:`CanonicalPatient`."""

from __future__ import annotations

from datetime import date
from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_national_id,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.patient import CanonicalPatient


def _decode_sex(value: object | None, *, source_id: str, ctx: TransformContext) -> Sex:
    """Best-effort mapping from Gesdén's ``Sexo`` column.

    Observed values in Spanish dental PMS deployments are typically ``H``
    (hombre) and ``M`` (mujer). ``V`` (varón) and ``F`` (femenino) also
    appear in some clinics. Anything else is emitted as ``UNKNOWN`` with a
    warning so the destination can flag the row for manual review.
    """
    if value is None:
        return Sex.UNKNOWN
    token = str(value).strip().upper()
    if token in ("H", "V"):
        return Sex.MALE
    if token in ("M", "F"):
        return Sex.FEMALE
    if token == "":
        return Sex.UNKNOWN
    ctx.warnings.add(
        severity="warn",
        code="patient.sex.unknown_token",
        message=f"unmapped Sexo value: {token!r}",
        entity_type="patient",
        source_id=source_id,
    )
    return Sex.UNKNOWN


def _derive_deactivated_at(inactivo: object | None) -> date | None:
    """Gesdén stores soft-delete via ``Inactivo`` (a date in older builds
    and a bit/int flag in newer ones). Treat datetime-like values as a
    deactivation date and bit-like values as ``None`` — the boolean
    fact is carried in ``raw_source_data`` for importers that need it.
    """
    return clean_date(inactivo)


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPatient:
    """Convert a raw ``Pacientes`` row into the canonical model."""
    source_id = str(row["IdPac"])

    tenant_label = tenant_str(row.get("Guid_Tenant"))
    if ctx.tenant_label is None:
        ctx.tenant_label = tenant_label
    elif tenant_label is not None and tenant_label != ctx.tenant_label:
        ctx.warnings.add(
            severity="error",
            code="patient.tenant.mismatch",
            message=(
                f"row carries tenant {tenant_label!r} but the file is being "
                f"emitted for tenant {ctx.tenant_label!r}"
            ),
            entity_type="patient",
            source_id=source_id,
        )

    guardian_uuid = _resolve_client(row.get("IdCliTutor"), ctx)
    referrer_uuid = (
        derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPacReferidor"]))
        if row.get("IdPacReferidor") not in (None, "", 0)
        and str(row["IdPacReferidor"]) != source_id
        else None
    )

    return CanonicalPatient(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "patient", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_number=normalise_string(row.get("NumPac")),
        given_name=normalise_string(row.get("Nombre")),
        family_name=normalise_string(row.get("Apellidos")),
        national_id=normalise_national_id(row.get("NIF")),
        date_of_birth=clean_date(row.get("FecNacim")),
        sex=_decode_sex(row.get("Sexo"), source_id=source_id, ctx=ctx),
        registered_at=clean_date(row.get("FecAlta")),
        deactivated_at=_derive_deactivated_at(row.get("Inactivo")),
        deceased=bool(row.get("Exitus")),
        deceased_at=None,
        gdpr_consent=_bool_or_none(row.get("AceptaLOPD")),
        notes=normalise_string(row.get("Notas")),
        default_center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        default_professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        guardian_client_uuid=guardian_uuid,
        referrer_patient_uuid=referrer_uuid,
        tenant_label=tenant_label,
    )


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        # -1 is the "sin centro" sentinel documented in schema_map quirk #6.
        return None
    return ctx.id_mapping.resolve(ctx.source_system, entity_type, source_id)


def _resolve_client(source_id: object | None, ctx: TransformContext):
    if source_id in (None, "", 0):
        return None
    return ctx.id_mapping.resolve(ctx.source_system, "client", source_id)


def _bool_or_none(value: object | None) -> bool | None:
    if value is None:
        return None
    return bool(value)
