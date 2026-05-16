"""Transform ``TtosMedFases`` rows into :class:`CanonicalAppliedTreatmentPhase`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.applied_treatment import CanonicalAppliedTreatmentPhase
from dental_bridge.core.canonical.base import derive_canonical_uuid


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalAppliedTreatmentPhase:
    source_id = str(row["IdTtosMedFase"])
    return CanonicalAppliedTreatmentPhase(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "applied_treatment_phase", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        applied_treatment_uuid=derive_canonical_uuid(
            ctx.source_system, "applied_treatment", str(row["IdTtosMed"])
        ),
        phase_template_uuid=_resolve(ctx, "treatment_phase_template", row.get("IdTratamientoFase")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        auxiliary_professional_uuid=_resolve(ctx, "professional", row.get("IdColAux")),
        phase_number=coerce_int(row.get("NumFase")),
        status_code=coerce_int(row.get("Estado")),
        executed_on=clean_date(row.get("Fecha")),
        percent_to_bill=coerce_decimal(row.get("TpcFacturar")),
        notes=normalise_string(row.get("Notas")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
