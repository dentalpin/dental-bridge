"""Treatment catalog and applied treatment transformer tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.applied_treatments import (
    transform as transform_applied_treatment,
)
from dental_bridge.adapters.nemodent.transformers.catalog_items import (
    transform_treatment,
    transform_treatment_variant,
)
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context() -> TransformContext:
    mapping = IdMapping()
    mapping.register("nemodent", "catalog_item", "MASTER_PROCEDURE_TYPES:5")
    mapping.register("nemodent", "treatment_catalog_item", "10")
    mapping.register("nemodent", "treatment_catalog_variant", "PROCEDURES:1:10")
    mapping.register("nemodent", "patient", "patient-1")
    mapping.register("nemodent", "professional", "D01")
    mapping.register("nemodent", "center", "clinic-1")
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=mapping,
        warnings=WarningRegistry(),
        center_source_ids=["clinic-1"],
    )


def test_master_procedure_maps_to_canonical_treatment() -> None:
    context = _context()

    treatment = transform_treatment(
        {
            "ID": 10,
            "Description": "Restoration",
            "Amount": Decimal("45.00"),
            "TypeID": 5,
            "NemodentCode": "R10",
            "IsDisabled": False,
        },
        context,
    )

    assert treatment is not None
    assert treatment.source_id == "10"
    assert treatment.description == "Restoration"
    assert treatment.reference_price == Decimal("45.00")


def test_procedure_tariff_maps_to_catalog_variant() -> None:
    context = _context()

    variant = transform_treatment_variant(
        {
            "Class": "1",
            "ID": 10,
            "Code": "R10-A",
            "Description": "Restoration private",
            "PatientAmount": Decimal("45.00"),
            "InsuranceAmount": Decimal("0"),
            "IsDisabled": False,
        },
        context,
    )

    assert variant is not None
    assert variant.source_id == "PROCEDURES:1:10"
    assert variant.treatment_uuid == context.id_mapping.resolve(
        "nemodent", "treatment_catalog_item", "10"
    )
    assert variant.tariff_code == "1"


def test_applied_treatment_joins_history_and_resolves_canonical_links() -> None:
    context = _context()
    row = {
        "ProcedureGUID": "procedure-1",
        "HistoryGUID": "procedure-1",
        "ProcedureID": "10",
        "ProcedureClass": "1",
        "PersonnelID": "D01",
        "Personnel1ID": None,
        "Personnel2ID": None,
        "Amount": Decimal("45.00"),
        "Discount": Decimal("10"),
        "Debit": Decimal("30.00"),
        "InsuranceAmount": Decimal("15.00"),
        "Deposit": Decimal("0"),
        "Phase": 1,
        "VAT": Decimal("0"),
        "PatientGUID": "patient-1",
        "HistoryDate": date(2025, 3, 10),
        "HistoryComments": "synthetic note",
        "HistorySessionGUID": None,
        "HistoryOrder": 1,
        "HistoryRegionType": None,
        "HistoryRegion": None,
        "HistoryRegion2": None,
        "HistorySubRegions": None,
        "TaskCode": "T01",
        "TaskStatus": 5,
        "TaskEndDate": date(2025, 3, 10),
        "TaskParentGUID": None,
    }

    applied = transform_applied_treatment(row, context)

    assert applied is not None
    assert applied.source_id == "procedure-1"
    assert applied.patient_uuid == context.id_mapping.resolve("nemodent", "patient", "patient-1")
    assert applied.treatment_variant_uuid == context.id_mapping.resolve(
        "nemodent", "treatment_catalog_variant", "PROCEDURES:1:10"
    )
    assert applied.amount == Decimal("45.00")
    assert applied.discount_percent == Decimal("10")
    assert applied.pending_amount == Decimal("30.00")
    assert applied.mutua_amount == Decimal("15.00")
    assert applied.start_date == date(2025, 3, 10)
    assert applied.raw_source_data["PATIENT_PROCEDURES"]["ProcedureID"] == "10"
    assert applied.raw_source_data["PATIENT_HISTORY"]["GUID"] == "procedure-1"


def test_applied_treatment_without_history_is_exported_with_warning() -> None:
    context = _context()

    applied = transform_applied_treatment(
        {
            "ProcedureGUID": "procedure-orphan",
            "HistoryGUID": None,
            "PatientGUID": None,
            "ProcedureID": "10",
            "ProcedureClass": "1",
        },
        context,
    )

    assert applied is not None
    assert applied.source_id == "procedure-orphan"
    assert applied.patient_uuid is None
    assert applied.start_date is None
    assert applied.raw_source_data["PATIENT_HISTORY"]["GUID"] is None
    assert [warning.code for warning in context.warnings] == ["applied_treatment.history_missing"]
