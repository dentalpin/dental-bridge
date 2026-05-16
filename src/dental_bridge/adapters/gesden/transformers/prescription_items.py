"""Transform ``RecetasDet`` rows into :class:`CanonicalPrescriptionItem`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.clinical_secondary import CanonicalPrescriptionItem


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _resolve_catalog(ctx: TransformContext, kind: str, source_id: object | None):
    if source_id in (None, "", 0):
        return None
    return derive_canonical_uuid(ctx.source_system, "catalog_item", f"{kind}:{source_id}")


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPrescriptionItem:
    source_id = str(row["IdRecetaDet"])
    return CanonicalPrescriptionItem(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "prescription_item", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        prescription_uuid=derive_canonical_uuid(
            ctx.source_system, "prescription", str(row["IdReceta"])
        ),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        drug_uuid=_resolve_catalog(ctx, "drug", row.get("IdTrat")),
        drug_description=normalise_string(row.get("DescFarmaco")),
        pattern=normalise_string(row.get("Pauta")),
        posology=normalise_string(row.get("Posologia")),
        units=coerce_int(row.get("Unidades")),
        packages=coerce_int(row.get("Envases")),
        duration=normalise_string(row.get("Duracion")),
        dispense_order=coerce_int(row.get("OrdenDisp")),
        previous_dispensation=normalise_string(row.get("DispPrev")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
