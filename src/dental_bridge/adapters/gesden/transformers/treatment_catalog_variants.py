"""Transform a ``Tratamientos_Tarifas`` row into :class:`CanonicalTreatmentCatalogVariant`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.treatment import CanonicalTreatmentCatalogVariant


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalTreatmentCatalogVariant:
    source_id = str(row["IdTratamientoTarifa"])

    specialty_uuid = None
    if row.get("IdTipoEspec") not in (None, "", 0):
        specialty_uuid = derive_canonical_uuid(
            ctx.source_system, "catalog_item", f"specialty:{row['IdTipoEspec']}"
        )

    return CanonicalTreatmentCatalogVariant(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "treatment_catalog_variant", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        treatment_uuid=derive_canonical_uuid(
            ctx.source_system, "treatment_catalog_item", str(row["IdTratamiento"])
        ),
        tariff_code=str(row["IdTarifa"]) if row.get("IdTarifa") not in (None, "") else None,
        code=normalise_string(row.get("CodTto")),
        specialty_uuid=specialty_uuid,
        deactivated=bool(row.get("Inactivo")) if row.get("Inactivo") is not None else False,
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
