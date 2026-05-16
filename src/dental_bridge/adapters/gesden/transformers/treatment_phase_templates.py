"""Transform ``TratamientosFases`` rows into :class:`CanonicalTreatmentPhaseTemplate`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.treatment import CanonicalTreatmentPhaseTemplate


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalTreatmentPhaseTemplate:
    source_id = str(row["IdTratamientoFase"])
    return CanonicalTreatmentPhaseTemplate(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "treatment_phase_template", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        treatment_uuid=derive_canonical_uuid(
            ctx.source_system, "treatment_catalog_item", str(row["IdTratamiento"])
        ),
        description=normalise_string(row.get("DescripMed")),
        observations=normalise_string(row.get("Observaciones")),
        duration_minutes=coerce_int(row.get("Duracion")),
        execution_order=coerce_int(row.get("OrdenEjecucion")),
        percent_to_bill=coerce_decimal(row.get("TpcFacturar")),
        min_days=coerce_int(row.get("MinDias")),
        max_days=coerce_int(row.get("MaxDias")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
