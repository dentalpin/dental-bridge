"""Transform ``TTratamientos`` rows into :class:`CanonicalPharmacologicalHistory`."""

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
from dental_bridge.core.canonical.clinical_secondary import (
    CanonicalPharmacologicalHistory,
)


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _resolve_catalog(ctx: TransformContext, kind: str, source_id: object | None):
    if source_id in (None, "", 0):
        return None
    return derive_canonical_uuid(ctx.source_system, "catalog_item", f"{kind}:{source_id}")


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPharmacologicalHistory:
    composite = f"{row['IdPac']}:{row['IdTrat']}"
    return CanonicalPharmacologicalHistory(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "pharmacological_history", composite
        ),
        source_system=ctx.source_system,
        source_id=composite,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPac"])),
        professional_uuid=_resolve(ctx, "professional", row.get("IdUsu")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        drug_uuid=_resolve_catalog(ctx, "drug", row.get("IdFarmaco")),
        drug_description=normalise_string(row.get("DescFarmaco")),
        dose=normalise_string(row.get("Dosis")),
        dosage=normalise_string(row.get("Dosificacion")),
        administration_route=normalise_string(row.get("ViaAdmin")),
        frequency=normalise_string(row.get("Frecuencia")),
        observations=normalise_string(row.get("Observac")),
        record_kind=coerce_int(row.get("Tipo")),
        public=bool(row.get("Publico")) if row.get("Publico") is not None else None,
        start_date=clean_date(row.get("Fecha")),
        end_date=clean_date(row.get("FecFin")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
