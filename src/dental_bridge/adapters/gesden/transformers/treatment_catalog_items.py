"""Transform a Gesdén ``Tratamientos`` row into :class:`CanonicalTreatmentCatalogItem`."""

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
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.treatment import CanonicalTreatmentCatalogItem


def _bool_or_default(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalTreatmentCatalogItem:
    source_id = str(row["IdTratamiento"])

    specialty_uuid = None
    if row.get("IdTipoEspec") not in (None, "", 0):
        specialty_uuid = derive_canonical_uuid(
            ctx.source_system, "catalog_item", f"specialty:{row['IdTipoEspec']}"
        )

    odontogram_kind_uuid = None
    if row.get("IdTipoODG") not in (None, "", 0):
        odontogram_kind_uuid = derive_canonical_uuid(
            ctx.source_system, "catalog_item", f"odontogram_kind:{row['IdTipoODG']}"
        )

    return CanonicalTreatmentCatalogItem(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "treatment_catalog_item", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        code=normalise_string(row.get("Codigo")),
        short_name=normalise_string(row.get("DescripAgd")),
        description=normalise_string(row.get("DescripMed")),
        patient_facing_description=normalise_string(row.get("DescripPac")),
        agenda_description=normalise_string(row.get("DescripAgd")),
        specialty_uuid=specialty_uuid,
        odontogram_kind_uuid=odontogram_kind_uuid,
        duration_minutes=coerce_int(row.get("Duracion")),
        number_of_phases=coerce_int(row.get("NumFases")),
        reference_price=coerce_decimal(row.get("PrecioReferencia")),
        deactivated=_bool_or_default(row.get("Inactivo")),
        valid_from=clean_date(row.get("Desde")),
        valid_until=clean_date(row.get("Hasta")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
