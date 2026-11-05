"""Nemodent patient-alert mapping keeps unknown type codes in raw data."""

from __future__ import annotations

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.patient_alerts import transform
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context(*, include_patient: bool = True) -> TransformContext:
    id_mapping = IdMapping()
    if include_patient:
        id_mapping.register("nemodent", "patient", "patient-1")
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=id_mapping,
        warnings=WarningRegistry(),
        tenant_label="fixture",
    )


def test_alert_maps_description_and_preserves_unknown_type() -> None:
    context = _context()

    alert = transform(
        {"GUID": "patient-1", "Description": "Synthetic alert", "Type": 7},
        context,
    )

    assert alert is not None
    assert alert.source_id == "patient-1"
    assert alert.canonical_uuid == derive_canonical_uuid("nemodent", "patient_alert", "patient-1")
    assert alert.patient_uuid == context.id_mapping.resolve("nemodent", "patient", "patient-1")
    assert alert.text == "Synthetic alert"
    assert alert.flagged is True
    assert alert.alert_number is None
    assert alert.raw_source_data["Type"] == 7


def test_alert_without_exported_patient_is_omitted_with_warning() -> None:
    context = _context(include_patient=False)

    alert = transform(
        {"GUID": "patient-1", "Description": "Synthetic alert", "Type": 7},
        context,
    )

    assert alert is None
    assert [warning.code for warning in context.warnings] == ["patient_alert.patient_unresolved"]
