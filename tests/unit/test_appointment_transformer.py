"""Tests for the Gesdén appointment transformer."""

from __future__ import annotations

from datetime import date, time

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.appointments import transform
from dental_bridge.core.canonical.appointment import AppointmentStatus
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def _baseline_row() -> dict[str, object]:
    return {
        "IdUsu": 7,
        "IdOrden": 100_001,
        "IdCita": 100_001,
        "IdPac": 42,
        "IdCli": 50,
        "IdCentro": 1,
        "IdCol": 7,
        "IdSitC": 3,
        "IdBox": 2,
        "Fecha": 46155,  # 2026-05-13 in OLE-epoch days
        "Hora": 32400,  # 09:00 in seconds-since-midnight
        "Duracion": 1800,  # 30 minutes, stored in seconds
        "Texto": "Limpieza + revisión",
        "IdCitasP": None,
        "FecAlta": None,
        "Guid_Tenant": "abc",
    }


def test_baseline_appointment() -> None:
    a = transform(_baseline_row(), _ctx())
    assert a.scheduled_date == date(2026, 5, 13)
    assert a.scheduled_time == time(9, 0)
    assert a.duration_minutes == 30
    assert a.notes == "Limpieza + revisión"
    assert a.coarse_status is AppointmentStatus.ATTENDED


def test_all_canonical_refs_resolved() -> None:
    a = transform(_baseline_row(), _ctx())
    assert a.patient_uuid == derive_canonical_uuid("gesden", "patient", "42")
    assert a.client_uuid == derive_canonical_uuid("gesden", "client", "50")
    assert a.center_uuid == derive_canonical_uuid("gesden", "center", "1")
    assert a.professional_uuid == derive_canonical_uuid("gesden", "professional", "7")
    assert a.chair_uuid == derive_canonical_uuid("gesden", "catalog_item", "chair:2")
    assert a.status_uuid == derive_canonical_uuid("gesden", "catalog_item", "appointment_status:3")


def test_recurrence_link_resolved() -> None:
    row = _baseline_row()
    row["IdCitasP"] = 17
    a = transform(row, _ctx())
    assert a.recurrence_uuid == derive_canonical_uuid("gesden", "appointment_recurrence", "17")


def test_no_recurrence_when_id_zero() -> None:
    row = _baseline_row()
    row["IdCitasP"] = 0
    a = transform(row, _ctx())
    assert a.recurrence_uuid is None


def test_center_minus_one_is_null() -> None:
    row = _baseline_row()
    row["IdCentro"] = -1
    a = transform(row, _ctx())
    assert a.center_uuid is None


def test_invalid_date_int_becomes_null() -> None:
    row = _baseline_row()
    row["Fecha"] = 0
    a = transform(row, _ctx())
    assert a.scheduled_date is None


def test_invalid_time_int_becomes_null() -> None:
    row = _baseline_row()
    row["Hora"] = 999_999  # > 86400 seconds in a day
    a = transform(row, _ctx())
    assert a.scheduled_time is None
