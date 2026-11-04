"""Transform appointment statuses and physical locations to catalog items."""

from __future__ import annotations

import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import (
    APPOINTMENT_STATUS_COLUMNS,
    CLINIC_LOCATION_COLUMNS,
    MASTER_PROCEDURE_COLUMNS,
    MASTER_PROCEDURE_TYPE_COLUMNS,
    PROCEDURE_COLUMNS,
)
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.catalog_item import (
    CanonicalCatalogItem,
    CatalogKind,
)
from dental_bridge.core.canonical.treatment import (
    CanonicalTreatmentCatalogItem,
    CanonicalTreatmentCatalogVariant,
)

_CHAIR_WORDS = frozenset(
    {"chair", "box", "cab", "cabinet", "cabinete", "gabinete", "silla", "sillon", "operatorio"}
)


def transform_location(
    row: dict[str, Any], context: TransformContext
) -> CanonicalCatalogItem | None:
    source_id = text(row.get("ID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="catalog.location_missing_source_id",
            message="Nemodent location row has no ID and was omitted.",
            entity_type="catalog_item",
        )
        return None

    location_type = text(row.get("Type"))
    type_name = context.location_type_names.get(location_type or "")
    is_chair = _is_chair_type(type_name)
    if type_name is None:
        context.warnings.add(
            severity="warn",
            code="catalog.location_type_unresolved",
            message="Nemodent location type has no matching lookup row.",
            entity_type="catalog_item",
            source_id=f"CLINIC_LOCATIONS:{source_id}",
        )
    elif type_name is not None and not is_chair:
        context.warnings.add(
            severity="info",
            code="catalog.location_not_a_chair",
            message="Nemodent location was not classified as a chair; appointments keep its source ID.",
            entity_type="catalog_item",
            source_id=f"CLINIC_LOCATIONS:{source_id}",
        )

    source_key = f"CLINIC_LOCATIONS:{source_id}"
    if is_chair:
        context.chair_source_ids.add(source_id)
    return CanonicalCatalogItem(
        **canonical_envelope(
            context,
            "catalog_item",
            source_key,
            {key: row.get(key) for key in CLINIC_LOCATION_COLUMNS},
        ),
        kind=CatalogKind.CHAIR if is_chair else CatalogKind.OTHER,
        code=source_id,
        name=text(row.get("Name")),
        description=type_name,
        tenant_label=context.tenant_label,
    )


def transform_appointment_status(
    row: dict[str, Any], context: TransformContext
) -> CanonicalCatalogItem | None:
    source_id = text(row.get("ID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="catalog.appointment_status_missing_source_id",
            message="Nemodent appointment status has no ID and was omitted.",
            entity_type="catalog_item",
        )
        return None

    name = text(row.get("Name"))
    context.appointment_status_labels[source_id] = name or ""
    source_key = f"APPOINTMENT_STATUS:{source_id}"
    return CanonicalCatalogItem(
        **canonical_envelope(
            context,
            "catalog_item",
            source_key,
            {key: row.get(key) for key in APPOINTMENT_STATUS_COLUMNS},
        ),
        kind=CatalogKind.APPOINTMENT_STATUS,
        code=source_id,
        name=name,
        tenant_label=context.tenant_label,
    )


def transform_specialty(
    row: dict[str, Any], context: TransformContext
) -> CanonicalCatalogItem | None:
    source_id = text(row.get("TypeID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="catalog.specialty_missing_source_id",
            message="Nemodent procedure type has no TypeID and was omitted.",
            entity_type="catalog_item",
        )
        return None
    return CanonicalCatalogItem(
        **canonical_envelope(
            context,
            "catalog_item",
            f"MASTER_PROCEDURE_TYPES:{source_id}",
            {key: row.get(key) for key in MASTER_PROCEDURE_TYPE_COLUMNS},
        ),
        kind=CatalogKind.SPECIALTY,
        code=text(row.get("NemodentCode")) or source_id,
        name=text(row.get("Name")),
        tenant_label=context.tenant_label,
    )


def transform_treatment(
    row: dict[str, Any], context: TransformContext
) -> CanonicalTreatmentCatalogItem | None:
    source_id = text(row.get("ID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="treatment_catalog.missing_source_id",
            message="Nemodent master procedure has no ID and was omitted.",
            entity_type="treatment_catalog_item",
        )
        return None
    type_id = text(row.get("TypeID"))
    specialty_uuid = (
        context.id_mapping.resolve(
            context.source_system,
            "catalog_item",
            f"MASTER_PROCEDURE_TYPES:{type_id}",
            require_known=True,
        )
        if type_id
        else None
    )
    if type_id and specialty_uuid is None:
        context.warnings.add(
            severity="warn",
            code="treatment_catalog.specialty_unresolved",
            message="Nemodent procedure type was not included in the catalog.",
            entity_type="treatment_catalog_item",
            source_id=source_id,
        )
    return CanonicalTreatmentCatalogItem(
        **canonical_envelope(
            context,
            "treatment_catalog_item",
            source_id,
            {key: row.get(key) for key in MASTER_PROCEDURE_COLUMNS},
        ),
        code=text(row.get("NemodentCode")) or source_id,
        description=text(row.get("Description")),
        specialty_uuid=specialty_uuid,
        reference_price=_decimal(row.get("Amount")),
        deactivated=bool(row.get("IsDisabled", False)),
        tenant_label=context.tenant_label,
    )


def transform_treatment_variant(
    row: dict[str, Any], context: TransformContext
) -> CanonicalTreatmentCatalogVariant | None:
    procedure_id = text(row.get("ID"))
    procedure_class = text(row.get("Class"))
    if procedure_id is None or procedure_class is None:
        context.warnings.add(
            severity="error",
            code="treatment_variant.missing_source_id",
            message="Nemodent procedure variant is missing Class or ID and was omitted.",
            entity_type="treatment_catalog_variant",
        )
        return None

    treatment_uuid = context.id_mapping.resolve(
        context.source_system,
        "treatment_catalog_item",
        procedure_id,
        require_known=True,
    )
    if treatment_uuid is None:
        context.warnings.add(
            severity="warn",
            code="treatment_variant.master_unresolved",
            message="Nemodent procedure variant has no included master procedure.",
            entity_type="treatment_catalog_variant",
            source_id=f"{procedure_class}:{procedure_id}",
        )
        return None

    return CanonicalTreatmentCatalogVariant(
        **canonical_envelope(
            context,
            "treatment_catalog_variant",
            f"PROCEDURES:{procedure_class}:{procedure_id}",
            {key: row.get(key) for key in PROCEDURE_COLUMNS},
        ),
        treatment_uuid=treatment_uuid,
        tariff_code=procedure_class,
        code=text(row.get("Code")),
        deactivated=bool(row.get("IsDisabled", False)),
        tenant_label=context.tenant_label,
    )


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _is_chair_type(type_name: str | None) -> bool:
    if type_name is None:
        return False
    normalized = unicodedata.normalize("NFKD", type_name).encode("ascii", "ignore").decode()
    words = set(normalized.casefold().replace("-", " ").replace("_", " ").split())
    return bool(words & _CHAIR_WORDS)
