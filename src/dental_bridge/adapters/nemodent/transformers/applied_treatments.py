"""Transform linked Nemodent history/procedure rows to applied treatments."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    as_date,
    canonical_envelope,
    text,
    warn_once,
)
from dental_bridge.core.canonical.applied_treatment import CanonicalAppliedTreatment


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalAppliedTreatment | None:
    source_id = text(row.get("ProcedureGUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="applied_treatment.missing_source_id",
            message="Nemodent patient procedure has no GUID and was omitted.",
            entity_type="applied_treatment",
        )
        return None

    if text(row.get("HistoryGUID")) is None:
        context.warnings.add(
            severity="warn",
            code="applied_treatment.history_missing",
            message="Nemodent procedure has no matching history row; it was exported without patient/date.",
            entity_type="applied_treatment",
            source_id=source_id,
        )

    patient_uuid = _resolve(
        context,
        entity_type="patient",
        source_id=row.get("PatientGUID"),
    )
    if row.get("PatientGUID") is not None and patient_uuid is None:
        context.warnings.add(
            severity="warn",
            code="applied_treatment.patient_unresolved",
            message="Nemodent procedure references a patient not included in the export.",
            entity_type="applied_treatment",
            source_id=source_id,
        )

    professional_id = text(row.get("PersonnelID")) or text(row.get("Personnel1ID"))
    professional_uuid = _resolve(
        context,
        entity_type="professional",
        source_id=professional_id,
    )
    auxiliary_uuid = _resolve(
        context,
        entity_type="professional",
        source_id=row.get("Personnel2ID"),
    )

    procedure_id = text(row.get("ProcedureID"))
    procedure_class = text(row.get("ProcedureClass"))
    variant_uuid = None
    if procedure_id and procedure_class:
        variant_uuid = _resolve(
            context,
            entity_type="treatment_catalog_variant",
            source_id=f"PROCEDURES:{procedure_class}:{procedure_id}",
        )
        if variant_uuid is None:
            warn_once(
                context,
                f"applied_treatment.variant_unresolved:{procedure_class}:{procedure_id}",
                severity="warn",
                code="applied_treatment.variant_unresolved",
                message="Nemodent procedure has no matching exported catalog variant.",
                entity_type="applied_treatment",
            )

    raw = {
        "PATIENT_PROCEDURES": {
            key: row.get(source_key)
            for key, source_key in (
                ("GUID", "ProcedureGUID"),
                ("ProcedureID", "ProcedureID"),
                ("Class", "ProcedureClass"),
                ("PersonnelID", "PersonnelID"),
                ("Personnel1ID", "Personnel1ID"),
                ("Personnel2ID", "Personnel2ID"),
                ("Amount", "Amount"),
                ("Discount", "Discount"),
                ("Debit", "Debit"),
                ("InsuranceAmount", "InsuranceAmount"),
                ("Deposit", "Deposit"),
                ("Phase", "Phase"),
                ("VAT", "VAT"),
            )
        },
        "PATIENT_HISTORY": {
            key: row.get(source_key)
            for key, source_key in (
                ("GUID", "HistoryGUID"),
                ("GUID_PATIENT", "PatientGUID"),
                ("Date", "HistoryDate"),
                ("Comments", "HistoryComments"),
                ("GUID_SESSION", "HistorySessionGUID"),
                ("Order", "HistoryOrder"),
                ("RegionType", "HistoryRegionType"),
                ("Region", "HistoryRegion"),
                ("Region2", "HistoryRegion2"),
                ("SubRegions", "HistorySubRegions"),
            )
        },
        "PATIENT_TASKS": {
            key: row.get(source_key)
            for key, source_key in (
                ("GUID", "ProcedureGUID"),
                ("TaskCode", "TaskCode"),
                ("Status", "TaskStatus"),
                ("EndDate", "TaskEndDate"),
                ("GUID_PARENT", "TaskParentGUID"),
            )
        },
    }
    return CanonicalAppliedTreatment(
        **canonical_envelope(context, "applied_treatment", source_id, raw),
        patient_uuid=patient_uuid,
        professional_uuid=professional_uuid,
        auxiliary_professional_uuid=auxiliary_uuid,
        center_uuid=_default_center_uuid(context),
        treatment_variant_uuid=variant_uuid,
        status_code=_optional_int(row.get("TaskStatus")),
        start_date=as_date(row.get("HistoryDate")),
        end_date=as_date(row.get("TaskEndDate")),
        amount=_decimal(row.get("Amount")),
        discount_percent=_decimal(row.get("Discount")),
        pending_amount=_decimal(row.get("Debit")),
        mutua_amount=_decimal(row.get("InsuranceAmount")),
        notes=text(row.get("HistoryComments")),
        tenant_label=context.tenant_label,
    )


def _resolve(
    context: TransformContext, *, entity_type: str, source_id: object | None
) -> UUID | None:
    normalized_id = text(source_id)
    if normalized_id is None:
        return None
    return context.id_mapping.resolve(
        context.source_system,
        entity_type,
        normalized_id,
        require_known=True,
    )


def _default_center_uuid(context: TransformContext) -> UUID | None:
    if len(context.center_source_ids) != 1:
        return None
    return _resolve(
        context,
        entity_type="center",
        source_id=context.center_source_ids[0],
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
