"""Catalog transformers preserve source ids and only classify known chair types."""

from __future__ import annotations

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.catalog_items import (
    transform_appointment_status,
    transform_location,
    transform_specialty,
)
from dental_bridge.core.canonical.catalog_item import CatalogKind
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context() -> TransformContext:
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
        location_type_names={"R": "Gabinete"},
    )


def test_location_uses_a_prefixed_source_key_and_recognized_kind() -> None:
    context = _context()

    item = transform_location({"ID": "01", "Name": "Box 1", "Type": "R"}, context)

    assert item is not None
    assert item.source_id == "CLINIC_LOCATIONS:01"
    assert item.kind is CatalogKind.CHAIR
    assert "01" in context.chair_source_ids


def test_unknown_location_type_is_not_classified_as_chair() -> None:
    context = _context()
    context.location_type_names["X"] = "Reception"

    item = transform_location({"ID": "02", "Name": "Reception", "Type": "X"}, context)

    assert item is not None
    assert item.kind is CatalogKind.OTHER
    assert "02" not in context.chair_source_ids
    assert [warning.code for warning in context.warnings] == ["catalog.location_not_a_chair"]


def test_appointment_status_is_registered_for_coarse_status_mapping() -> None:
    context = _context()

    item = transform_appointment_status({"ID": 2, "Name": "Confirmada"}, context)

    assert item is not None
    assert item.kind is CatalogKind.APPOINTMENT_STATUS
    assert item.source_id == "APPOINTMENT_STATUS:2"
    assert context.appointment_status_labels["2"] == "Confirmada"


def test_procedure_type_maps_to_specialty_catalog_item() -> None:
    item = transform_specialty(
        {"TypeID": 5, "Name": "Dental", "NemodentCode": "D"},
        _context(),
    )

    assert item is not None
    assert item.kind is CatalogKind.SPECIALTY
    assert item.source_id == "MASTER_PROCEDURE_TYPES:5"
