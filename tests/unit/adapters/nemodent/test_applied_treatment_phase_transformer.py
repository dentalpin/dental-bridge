"""Clinical session rows map to canonical applied-treatment phases."""

from __future__ import annotations

from datetime import date, time

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.applied_treatment_phases import (
    transform,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context(*, include_parent: bool = True) -> TransformContext:
    id_mapping = IdMapping()
    if include_parent:
        id_mapping.register("nemodent", "applied_treatment", "task-1")
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=id_mapping,
        warnings=WarningRegistry(),
        tenant_label="fixture",
    )


def test_trace_maps_to_a_stable_canonical_session() -> None:
    context = _context()

    phase = transform(
        {
            "GUID_TASK": "task-1",
            "Date": date(2025, 4, 5),
            "StartTime": time(9, 30),
            "EndTime": time(10, 0),
            "Status": 2,
            "TraceCount": 3,
        },
        context,
    )

    assert phase is not None
    assert phase.source_id == "task-1:2025-04-05:09:30:00"
    assert phase.canonical_uuid == derive_canonical_uuid(
        "nemodent", "applied_treatment_phase", phase.source_id
    )
    assert phase.applied_treatment_uuid == context.id_mapping.resolve(
        "nemodent", "applied_treatment", "task-1"
    )
    assert phase.executed_on == date(2025, 4, 5)
    assert phase.status_code == 2
    assert phase.phase_number is None
    assert phase.raw_source_data["StartTime"] == "09:30:00"
    assert phase.raw_source_data["TraceCount"] == 3


def test_trace_without_parent_is_omitted_with_warning() -> None:
    context = _context(include_parent=False)

    phase = transform(
        {
            "GUID_TASK": "task-1",
            "Date": date(2025, 4, 5),
            "StartTime": time(9, 30),
            "Status": 2,
            "TraceCount": 1,
        },
        context,
    )

    assert phase is None
    assert [warning.code for warning in context.warnings] == [
        "applied_treatment_phase.parent_unresolved"
    ]


def test_trace_without_composite_key_is_omitted() -> None:
    context = _context()

    phase = transform({"GUID_TASK": "task-1", "Date": date(2025, 4, 5)}, context)

    assert phase is None
    assert [warning.code for warning in context.warnings] == [
        "applied_treatment_phase.missing_source_key"
    ]
