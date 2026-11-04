"""Budget transformers preserve source data and require canonical parents."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.nemodent import adapter as adapter_module
from dental_bridge.adapters.nemodent.adapter import NemodentAdapter
from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.budgets import (
    transform_budget,
    transform_budget_line,
)
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context() -> TransformContext:
    id_mapping = IdMapping()
    id_mapping.register("nemodent", "patient", "patient-1")
    id_mapping.register("nemodent", "professional", "007")
    id_mapping.register("nemodent", "center", "clinic-1")
    id_mapping.register("nemodent", "treatment_catalog_variant", "PROCEDURES:1:P10")
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=id_mapping,
        warnings=WarningRegistry(),
        center_source_ids=["clinic-1"],
        tenant_label="fixture",
    )


def test_budget_maps_header_and_caches_patient_for_its_lines() -> None:
    context = _context()
    row = {
        "GUID": "estimate-1",
        "GUID_PATIENT": "patient-1",
        "PersonnelID": "007",
        "Date": date(2025, 1, 2),
        "EstimateNumber": 34,
        "Name": "Treatment plan",
        "Comments": "Synthetic note",
        "Status": 2,
        "Amount": Decimal("125.50"),
        "SubTotal": Decimal("110.00"),
        "Discount": Decimal("5"),
        "Taxes": Decimal("15.50"),
        "Total": Decimal("125.50"),
        "Password": "must-not-export",
    }

    budget = transform_budget(row, context)

    assert budget is not None
    assert budget.source_id == "estimate-1"
    assert budget.patient_uuid == context.id_mapping.resolve("nemodent", "patient", "patient-1")
    assert budget.professional_uuid == context.id_mapping.resolve("nemodent", "professional", "007")
    assert budget.center_uuid == context.id_mapping.resolve("nemodent", "center", "clinic-1")
    assert budget.number == 34
    assert budget.quote_date == date(2025, 1, 2)
    assert budget.raw_source_data["Total"] == "125.50"
    assert "Password" not in budget.raw_source_data

    context.id_mapping.register("nemodent", "budget", budget.source_id)
    line = transform_budget_line(
        {
            "GUID": "estimate-line-1",
            "GUID_ESTIMATE": "estimate-1",
            "GUID_PARENT": None,
            "ProcedureID": "P10",
            "Class": "1",
            "Personnel1ID": "007",
            "Personnel2ID": None,
            "Status": 1,
            "Order": 3,
            "Amount": Decimal("125.50"),
            "Debit": Decimal("100.00"),
            "Discount": Decimal("5"),
            "InsuranceAmount": Decimal("20.00"),
            "Deposit": Decimal("10.00"),
        },
        context,
    )

    assert line is not None
    assert line.source_id == "estimate-line-1"
    assert line.budget_uuid == budget.canonical_uuid
    assert line.patient_uuid == budget.patient_uuid
    assert line.professional_uuid == budget.professional_uuid
    assert line.treatment_variant_uuid == context.id_mapping.resolve(
        "nemodent", "treatment_catalog_variant", "PROCEDURES:1:P10"
    )
    assert line.order_within_budget == 3
    assert line.unit_amount == Decimal("125.50")
    assert line.discount_percent == Decimal("5")
    assert line.raw_source_data["Amount"] == "125.50"
    assert line.raw_source_data["Discount"] == "5"
    assert line.raw_source_data["Deposit"] == "10.00"


def test_budget_line_without_exported_parent_is_omitted() -> None:
    context = _context()

    line = transform_budget_line(
        {
            "GUID": "orphan-line",
            "GUID_ESTIMATE": "missing-budget",
            "ProcedureID": None,
            "Class": None,
        },
        context,
    )

    assert line is None
    assert [warning.code for warning in context.warnings] == ["budget_line.budget_unresolved"]


def test_adapter_streams_budget_headers_before_lines(monkeypatch) -> None:
    rows = {
        "ESTIMATES": [
            {
                "GUID": "estimate-1",
                "GUID_PATIENT": "patient-1",
                "PersonnelID": "007",
                "EstimateNumber": 34,
            }
        ],
        "ESTIMATES_PROCEDURES": [
            {
                "GUID": "estimate-line-1",
                "GUID_ESTIMATE": "estimate-1",
                "ProcedureID": "P10",
                "Class": "1",
                "Order": 1,
                "Status": 1,
            }
        ],
    }

    def fake_iter_rows(_connection, *, table, columns):
        return iter(rows[table])

    class FakeConnection:
        def close(self) -> None:
            pass

    monkeypatch.setattr(adapter_module, "iter_rows", fake_iter_rows)
    adapter = NemodentAdapter()
    adapter._conn = FakeConnection()
    adapter.context.id_mapping.register("nemodent", "patient", "patient-1")
    adapter.context.id_mapping.register("nemodent", "professional", "007")
    adapter.context.id_mapping.register("nemodent", "center", "clinic-1")
    adapter.context.id_mapping.register("nemodent", "treatment_catalog_variant", "PROCEDURES:1:P10")
    adapter.context.center_source_ids.append("clinic-1")

    budgets = list(adapter.iter_entity("budget"))
    lines = list(adapter.iter_entity("budget_line"))

    assert [budget.source_id for budget in budgets] == ["estimate-1"]
    assert [line.source_id for line in lines] == ["estimate-line-1"]
    assert lines[0].budget_uuid == budgets[0].canonical_uuid
    adapter.close()
