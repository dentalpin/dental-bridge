"""Appointment mapping tests for slot/personnel expansion and status."""

from __future__ import annotations

from datetime import date, datetime

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.appointments import transform
from dental_bridge.core.canonical.appointment import AppointmentStatus
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def test_maps_slot_staff_status_duration_and_source_type_note() -> None:
    ids = IdMapping()
    ids.register("nemodent", "patient", "patient-guid")
    ids.register("nemodent", "professional", "dentist-1")
    ids.register("nemodent", "center", "clinic-guid")
    ids.register("nemodent", "catalog_item", "APPOINTMENT_STATUS:2")
    ids.register("nemodent", "catalog_item", "CLINIC_LOCATIONS:room-1")
    context = TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=ids,
        warnings=WarningRegistry(),
        tenant_label="clinic",
        appointment_status_labels={"2": "Confirmed"},
        chair_source_ids={"room-1"},
        center_source_ids=["clinic-guid"],
        appointment_type_labels={"type-guid": "Consulta"},
        appointment_type_durations={"type-guid": 30},
    )
    row = {
        "AppointmentGUID": "appointment-guid",
        "PatientGUID": "patient-guid",
        "AppointmentTypeGUID": "type-guid",
        "AppointmentDate": date(2026, 1, 2),
        "HeaderStart": datetime(1899, 12, 30, 9),
        "HeaderEnd": datetime(1899, 12, 30, 10),
        "AppointmentStatus": 2,
        "ResponsiblePersonnel": "backup",
        "HeaderLocation": "other-room",
        "SlotGUID": "slot-guid",
        "SlotStart": datetime(1899, 12, 30, 23, 45),
        "SlotEnd": datetime(1899, 12, 30, 0, 15),
        "SlotLocation": "room-1",
        "SlotSubject": "Visit",
        "SlotDescription": "Review",
        "SlotPersonnelAppointmentGUID": "appointment-guid",
        "SlotPersonnel": "dentist-1",
        "FollowupAppointmentGUID": "appointment-guid",
        "FollowupPatientGUID": "patient-guid",
        "FollowupCheckInDate": date(2026, 1, 2),
        "FollowupCheckInTime": datetime(1899, 12, 30, 9, 2),
        "FollowupCheckOutTime": datetime(1899, 12, 30, 10, 5),
        "FollowupTreatmentTimeSpent": 45,
    }

    appointment = transform(row, context)

    assert appointment is not None
    assert appointment.source_id == ("appointment-guid:slot:slot-guid:professional:dentist-1")
    assert appointment.patient_uuid == ids.resolve("nemodent", "patient", "patient-guid")
    assert appointment.professional_uuid == ids.resolve("nemodent", "professional", "dentist-1")
    assert appointment.center_uuid == ids.resolve("nemodent", "center", "clinic-guid")
    assert appointment.chair_uuid == ids.resolve(
        "nemodent", "catalog_item", "CLINIC_LOCATIONS:room-1"
    )
    assert appointment.coarse_status is AppointmentStatus.CONFIRMED
    assert appointment.duration_minutes == 30
    assert "Tipo de cita: Consulta" in (appointment.notes or "")
    assert appointment.raw_source_data["APPOINTMENTS"]["GUID_TYPE"] == "type-guid"
    assert appointment.raw_source_data["PATIENT_FOLLOWUP"]["TreatmentTimeSpent"] == 45
    assert appointment.scheduled_time.isoformat() == "23:45:00"


def test_skips_appointment_without_valid_start_time() -> None:
    context = TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )

    assert transform({"AppointmentGUID": "a-1"}, context) is None
    assert [warning.code for warning in context.warnings] == ["appointment.invalid_start"]


def test_same_slot_with_two_professionals_emits_distinct_appointment_ids() -> None:
    ids = IdMapping()
    ids.register("nemodent", "professional", "dentist-1")
    ids.register("nemodent", "professional", "dentist-2")
    context = TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=ids,
        warnings=WarningRegistry(),
    )
    base_row = {
        "AppointmentGUID": "appointment-guid",
        "AppointmentDate": date(2026, 1, 2),
        "SlotGUID": "slot-guid",
        "SlotStart": datetime(1899, 12, 30, 9),
        "SlotEnd": datetime(1899, 12, 30, 10),
        "SlotPersonnelAppointmentGUID": "appointment-guid",
    }

    first = transform({**base_row, "SlotPersonnel": "dentist-1"}, context)
    second = transform({**base_row, "SlotPersonnel": "dentist-2"}, context)

    assert first is not None
    assert second is not None
    assert first.source_id == "appointment-guid:slot:slot-guid:professional:dentist-1"
    assert second.source_id == "appointment-guid:slot:slot-guid:professional:dentist-2"
    assert first.canonical_uuid != second.canonical_uuid


def test_unassigned_slot_id_uses_only_source_appointment_and_slot_guids() -> None:
    context = TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )

    appointment = transform(
        {
            "AppointmentGUID": "B0AA8012-E7F4-45A0-9411-B0858C71F05D",
            "AppointmentDate": date(2026, 1, 2),
            "SlotGUID": "65B48AE7-687F-440D-AE6C-83CAC9BD21C8",
            "SlotStart": datetime(1899, 12, 30, 9),
            "SlotEnd": datetime(1899, 12, 30, 10),
        },
        context,
    )

    assert appointment is not None
    assert appointment.source_id == (
        "B0AA8012-E7F4-45A0-9411-B0858C71F05D:slot:65B48AE7-687F-440D-AE6C-83CAC9BD21C8"
    )
    assert "unassigned" not in appointment.source_id
    assert len(appointment.source_id) < 100
