"""Nemodent adapter contract tests that need no Access driver."""

from __future__ import annotations

from datetime import date, time
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from dental_bridge.adapters.nemodent import adapter as adapter_module
from dental_bridge.adapters.nemodent.adapter import NemodentAdapter
from dental_bridge.core.canonical.appointment import AppointmentStatus
from dental_bridge.core.pipeline.errors import WarningRegistry


def test_adapter_exposes_only_implemented_entities_in_dependency_order() -> None:
    adapter = NemodentAdapter()

    assert adapter.supported_entities() == adapter.default_entity_order()
    assert adapter.supported_entities() == [
        "center",
        "professional",
        "catalog_item",
        "patient",
        "appointment",
        "treatment_catalog_item",
        "treatment_catalog_variant",
        "applied_treatment",
        "applied_treatment_phase",
        "budget",
        "budget_line",
        "patient_alert",
        "fiscal_document",
        "fiscal_document_line",
    ]
    adapter.close()


def test_iteration_requires_connection() -> None:
    adapter = NemodentAdapter()

    with pytest.raises(RuntimeError, match="call connect"):
        list(adapter.iter_entity("patient"))


def test_appointment_slot_collision_keeps_first_and_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    warnings = WarningRegistry()
    adapter = NemodentAdapter(warnings=warnings)
    chair_uuid = uuid4()
    professional_uuid = uuid4()
    slot = {
        "chair_uuid": chair_uuid,
        "professional_uuid": professional_uuid,
        "scheduled_date": date(2026, 11, 10),
        "scheduled_time": time(9, 0),
        "coarse_status": AppointmentStatus.SCHEDULED,
    }
    appointments = [
        SimpleNamespace(entity_type="appointment", source_id="source-first", **slot),
        SimpleNamespace(entity_type="appointment", source_id="source-duplicate", **slot),
    ]
    _patch_appointment_rows(monkeypatch, adapter, appointments)

    exported = list(adapter.iter_entity("appointment"))

    assert [row.source_id for row in exported] == ["source-first"]
    assert [(warning.code, warning.source_id) for warning in warnings] == [
        ("appointment.duplicate_slot_omitted", "source-duplicate")
    ]


def test_same_time_for_different_professionals_is_not_a_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = NemodentAdapter()
    slot = {
        "chair_uuid": uuid4(),
        "scheduled_date": date(2026, 11, 10),
        "scheduled_time": time(9, 0),
        "coarse_status": AppointmentStatus.SCHEDULED,
    }
    appointments = [
        SimpleNamespace(
            entity_type="appointment",
            source_id="source-one",
            professional_uuid=uuid4(),
            **slot,
        ),
        SimpleNamespace(
            entity_type="appointment",
            source_id="source-two",
            professional_uuid=uuid4(),
            **slot,
        ),
    ]
    _patch_appointment_rows(monkeypatch, adapter, appointments)

    exported = list(adapter.iter_entity("appointment"))

    assert [row.source_id for row in exported] == ["source-one", "source-two"]
    assert len(adapter.context.warnings) == 0


def _patch_appointment_rows(
    monkeypatch: pytest.MonkeyPatch,
    adapter: NemodentAdapter,
    appointments: list[SimpleNamespace],
) -> None:
    rows = [{"index": index} for index in range(len(appointments))]
    monkeypatch.setattr(adapter_module, "iter_joined_rows", lambda _conn: iter(rows))
    monkeypatch.setattr(
        adapter_module.appointments,
        "transform",
        lambda row, _context: appointments[row["index"]],
    )
    adapter._conn = cast(Any, object())
