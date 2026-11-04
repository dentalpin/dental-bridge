"""Transform Nemodent estimate headers and lines to canonical budgets."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from dental_bridge.adapters.nemodent.extractors._allowlist import (
    BUDGET_COLUMNS,
    BUDGET_LINE_COLUMNS,
)
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    as_date,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.budget import CanonicalBudget, CanonicalBudgetLine


def transform_budget(row: dict[str, Any], context: TransformContext) -> CanonicalBudget | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="budget.missing_source_id",
            message="Nemodent estimate has no GUID and was omitted.",
            entity_type="budget",
        )
        return None

    patient_source_id = text(row.get("GUID_PATIENT"))
    if patient_source_id is not None:
        context.budget_patient_source_ids[source_id] = patient_source_id

    return CanonicalBudget(
        **canonical_envelope(
            context,
            "budget",
            source_id,
            {key: row.get(key) for key in BUDGET_COLUMNS},
        ),
        patient_uuid=_resolve(
            context,
            "patient",
            patient_source_id,
            entity_type_for_warning="budget",
            entity_source_id=source_id,
        ),
        professional_uuid=_resolve(
            context,
            "professional",
            row.get("PersonnelID"),
            entity_type_for_warning="budget",
            entity_source_id=source_id,
        ),
        center_uuid=_default_center_uuid(context),
        number=_optional_int(row.get("EstimateNumber")),
        title=text(row.get("Name")),
        notes=text(row.get("Comments")),
        quote_date=as_date(row.get("Date")),
        status_code=_optional_int(row.get("Status")),
        tenant_label=context.tenant_label,
    )


def transform_budget_line(
    row: dict[str, Any], context: TransformContext
) -> CanonicalBudgetLine | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="budget_line.missing_source_id",
            message="Nemodent estimate line has no GUID and was omitted.",
            entity_type="budget_line",
        )
        return None

    budget_source_id = text(row.get("GUID_ESTIMATE"))
    budget_uuid = (
        context.id_mapping.resolve(
            context.source_system,
            "budget",
            budget_source_id,
            require_known=True,
        )
        if budget_source_id is not None
        else None
    )
    if budget_uuid is None:
        context.warnings.add(
            severity="error",
            code="budget_line.budget_unresolved",
            message="Nemodent estimate line has no exported parent budget and was omitted.",
            entity_type="budget_line",
            source_id=source_id,
        )
        return None

    patient_source_id = (
        context.budget_patient_source_ids.get(budget_source_id)
        if budget_source_id is not None
        else None
    )
    procedure_id = text(row.get("ProcedureID"))
    procedure_class = text(row.get("Class"))
    treatment_variant_uuid = None
    if procedure_id is not None and procedure_class is not None:
        treatment_variant_uuid = _resolve(
            context,
            "treatment_catalog_variant",
            f"PROCEDURES:{procedure_class}:{procedure_id}",
            entity_type_for_warning="budget_line",
            entity_source_id=source_id,
        )

    return CanonicalBudgetLine(
        **canonical_envelope(
            context,
            "budget_line",
            source_id,
            {key: row.get(key) for key in BUDGET_LINE_COLUMNS},
        ),
        budget_uuid=budget_uuid,
        patient_uuid=_resolve(
            context,
            "patient",
            patient_source_id,
            entity_type_for_warning="budget_line",
            entity_source_id=source_id,
        ),
        professional_uuid=_resolve(
            context,
            "professional",
            row.get("Personnel1ID"),
            entity_type_for_warning="budget_line",
            entity_source_id=source_id,
        ),
        auxiliary_professional_uuid=_resolve(
            context,
            "professional",
            row.get("Personnel2ID"),
            entity_type_for_warning="budget_line",
            entity_source_id=source_id,
        ),
        treatment_variant_uuid=treatment_variant_uuid,
        order_within_budget=_optional_int(row.get("Order")),
        status_code=_optional_int(row.get("Status")),
        unit_amount=_decimal(row.get("Amount")),
        discount_percent=_decimal(row.get("Discount")),
        tenant_label=context.tenant_label,
    )


def _resolve(
    context: TransformContext,
    entity_type: str,
    source_id: object | None,
    *,
    entity_type_for_warning: str,
    entity_source_id: str,
) -> UUID | None:
    normalized_id = text(source_id)
    if normalized_id is None:
        return None
    resolved = context.id_mapping.resolve(
        context.source_system,
        entity_type,
        normalized_id,
        require_known=True,
    )
    if resolved is None:
        context.warnings.add(
            severity="warn",
            code=f"{entity_type_for_warning}.{entity_type}_unresolved",
            message=f"Nemodent budget references an unexported {entity_type}.",
            entity_type=entity_type_for_warning,
            source_id=entity_source_id,
        )
    return resolved


def _default_center_uuid(context: TransformContext) -> UUID | None:
    if len(context.center_source_ids) != 1:
        return None
    return context.id_mapping.resolve(
        context.source_system,
        "center",
        context.center_source_ids[0],
        require_known=True,
    )


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
