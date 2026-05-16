"""Transform ``Recalls`` rows into :class:`CanonicalRecall`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.clinical_secondary import CanonicalRecall


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _resolve_catalog(ctx: TransformContext, kind: str, source_id: object | None):
    if source_id in (None, "", 0):
        return None
    return derive_canonical_uuid(ctx.source_system, "catalog_item", f"{kind}:{source_id}")


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalRecall:
    composite = f"{row['IdPac']}:{row['NumRec']}"
    return CanonicalRecall(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "recall", composite),
        source_system=ctx.source_system,
        source_id=composite,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPac"])),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        reviewer_professional_uuid=_resolve(ctx, "professional", row.get("IdColRevisa")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        reason_uuid=_resolve_catalog(ctx, "recall_reason", row.get("IdMotivo")),
        result_uuid=_resolve_catalog(ctx, "recall_outcome", row.get("IdResultado")),
        related_budget_uuid=_resolve(ctx, "budget", row.get("Id_Presu")),
        related_applied_treatment_uuid=_resolve(ctx, "applied_treatment", row.get("Id_TtosMed")),
        origin_recall_uuid=(
            derive_canonical_uuid(
                ctx.source_system,
                "recall",
                f"{row['IdPac']}:{row['IdRecallOrigen']}",
            )
            if row.get("IdRecallOrigen") not in (None, "", 0)
            else None
        ),
        recall_number=coerce_int(row.get("NumRec")),
        scheduled_date=clean_date(row.get("Fecha")),
        contact_date=clean_date(row.get("FechaContacto")),
        contact_method_telephone=_bool(row.get("Telefono")),
        contact_method_letter=_bool(row.get("Carta")),
        contact_method_email=_bool(row.get("EMail")),
        contact_method_sms=_bool(row.get("SMS")),
        attended=_bool(row.get("Asistido")),
        scheduled=_bool(row.get("Citado")),
        status_code=coerce_int(row.get("IdEstado")),
        comments=normalise_string(row.get("Comentario")),
        observations=normalise_string(row.get("Observaciones")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
