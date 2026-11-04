"""Transform a Nemodent appointment header or slot/staff pair."""

from __future__ import annotations

import unicodedata
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    canonical_envelope,
    text,
    warn_once,
)
from dental_bridge.core.canonical.appointment import (
    AppointmentStatus,
    CanonicalAppointment,
)


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalAppointment | None:
    appointment_id = text(row.get("AppointmentGUID"))
    if appointment_id is None:
        context.warnings.add(
            severity="error",
            code="appointment.missing_source_id",
            message="Nemodent appointment row has no GUID and was omitted.",
            entity_type="appointment",
        )
        return None

    slot_id = text(row.get("SlotGUID"))
    slot_personnel_id = text(row.get("SlotPersonnel"))
    slot_personnel_appointment_id = text(row.get("SlotPersonnelAppointmentGUID"))
    if slot_personnel_id and slot_personnel_appointment_id != appointment_id:
        context.warnings.add(
            severity="warn",
            code="appointment.slot_personnel_parent_mismatch",
            message="Nemodent slot personnel row refers to a different appointment and was ignored.",
            entity_type="appointment",
            source_id=appointment_id,
        )
        slot_personnel_id = None
    professional_id = slot_personnel_id or text(row.get("ResponsiblePersonnel"))
    patient_id = text(row.get("PatientGUID"))
    if slot_id is None:
        source_id = appointment_id
    elif professional_id is None:
        source_id = f"{appointment_id}:slot:{slot_id}"
    else:
        source_id = f"{appointment_id}:slot:{slot_id}:professional:{professional_id}"

    appointment_date, start_time = _appointment_start(
        row.get("AppointmentDate"),
        row.get("SlotStart") if slot_id else row.get("HeaderStart"),
    )
    if appointment_date is None or start_time is None:
        context.warnings.add(
            severity="error",
            code="appointment.invalid_start",
            message="Nemodent appointment has no usable local date/start time and was omitted.",
            entity_type="appointment",
            source_id=source_id,
        )
        return None

    end_value = row.get("SlotEnd") if slot_id else row.get("HeaderEnd")
    duration = _duration_minutes(appointment_date, start_time, end_value)
    if end_value is not None and duration is None:
        context.warnings.add(
            severity="error",
            code="appointment.invalid_duration",
            message="Nemodent appointment end time is not after its start time.",
            entity_type="appointment",
            source_id=source_id,
        )
        return None
    appointment_type_id = text(row.get("AppointmentTypeGUID"))
    if duration is None and end_value is None and appointment_type_id:
        duration = context.appointment_type_durations.get(appointment_type_id)
    if end_value is None and duration is None:
        context.warnings.add(
            severity="warn",
            code="appointment.duration_missing",
            message="Nemodent appointment has no usable end time or type duration.",
            entity_type="appointment",
            source_id=source_id,
        )

    status_raw = row.get("AppointmentStatus")
    status_key = text(status_raw)
    status_label = context.appointment_status_labels.get(status_key or "")
    coarse_status = _coarse_status(status_label)
    if status_raw is not None and coarse_status is AppointmentStatus.UNKNOWN:
        warn_once(
            context,
            f"appointment.status_unmapped:{status_key}",
            severity="warn",
            code="appointment.status_unmapped",
            message="Nemodent appointment status could not be mapped to a canonical status.",
            entity_type="appointment",
        )

    status_uuid = None
    if status_key is not None:
        status_uuid = context.id_mapping.resolve(
            context.source_system,
            "catalog_item",
            f"APPOINTMENT_STATUS:{status_key}",
            require_known=True,
        )

    location_id = text(row.get("SlotLocation")) if slot_id else text(row.get("HeaderLocation"))
    chair_uuid = None
    if location_id and location_id in context.chair_source_ids:
        chair_uuid = context.id_mapping.resolve(
            context.source_system,
            "catalog_item",
            f"CLINIC_LOCATIONS:{location_id}",
            require_known=True,
        )

    patient_uuid = (
        context.id_mapping.resolve(context.source_system, "patient", patient_id, require_known=True)
        if patient_id
        else None
    )
    professional_uuid = (
        context.id_mapping.resolve(
            context.source_system,
            "professional",
            professional_id,
            require_known=True,
        )
        if professional_id
        else None
    )
    center_uuid = _default_center_uuid(context)
    if len(context.center_source_ids) > 1:
        warn_once(
            context,
            "appointment.center_ambiguous",
            severity="warn",
            code="appointment.center_ambiguous",
            message="Appointment rows do not identify a center and the source contains multiple centers.",
            entity_type="appointment",
        )
    if patient_id and patient_uuid is None:
        context.warnings.add(
            severity="warn",
            code="appointment.patient_unresolved",
            message="Nemodent appointment references a patient not included in the export.",
            entity_type="appointment",
            source_id=source_id,
        )
    if professional_id and professional_uuid is None:
        context.warnings.add(
            severity="warn",
            code="appointment.professional_unresolved",
            message="Nemodent appointment references personnel not included in the export.",
            entity_type="appointment",
            source_id=source_id,
        )
    if appointment_type_id is not None:
        warn_once(
            context,
            f"appointment.type_preserved:{appointment_type_id}",
            severity="info",
            code="appointment.type_preserved_as_source",
            message="Appointment type has no dedicated canonical field; its name is copied into notes when available.",
            entity_type="appointment",
        )

    subject = text(row.get("SlotSubject")) if slot_id else text(row.get("HeaderSubject"))
    description = (
        text(row.get("SlotDescription")) if slot_id else text(row.get("HeaderDescription"))
    )
    type_label = context.appointment_type_labels.get(appointment_type_id or "")
    notes = (
        "\n".join(
            part
            for part in (
                subject,
                description,
                f"Tipo de cita: {type_label}" if type_label else None,
            )
            if part
        )
        or None
    )
    raw: dict[str, Any] = {
        "APPOINTMENTS": {
            "GUID": row.get("AppointmentGUID"),
            "GUID_PATIENT": row.get("PatientGUID"),
            "GUID_ADMISSION": row.get("AdmissionGUID"),
            "GUID_TYPE": row.get("AppointmentTypeGUID"),
            "EXTERNAL_ID": row.get("ExternalID"),
            "Date": row.get("AppointmentDate"),
            "StartTime": row.get("HeaderStart"),
            "EndTime": row.get("HeaderEnd"),
            "Status": row.get("AppointmentStatus"),
            "ResponsiblePersonnel": row.get("ResponsiblePersonnel"),
            "LocationID": row.get("HeaderLocation"),
            "Subject": row.get("HeaderSubject"),
            "Description": row.get("HeaderDescription"),
            "Emergency": row.get("Emergency"),
            "Flags": row.get("Flags"),
            "ModificationDate": row.get("ModificationDate"),
        }
    }
    if slot_id:
        raw["APPOINTMENT_SLOTS"] = {
            "GUID": row.get("SlotGUID"),
            "GUID_APPOINTMENT": row.get("AppointmentGUID"),
            "StartTime": row.get("SlotStart"),
            "EndTime": row.get("SlotEnd"),
            "LocationID": row.get("SlotLocation"),
            "Subject": row.get("SlotSubject"),
            "Description": row.get("SlotDescription"),
            "TASK_GUID": row.get("SlotTaskGUID"),
        }
        if row.get("SlotPersonnel") is not None:
            raw["APPOINTMENT_SLOT_PERSONNEL"] = {
                "GUID_APPOINTMENT": row.get("SlotPersonnelAppointmentGUID"),
                "GUID_SLOT": row.get("SlotGUID"),
                "PersonnelID": row.get("SlotPersonnel"),
            }

    if row.get("FollowupAppointmentGUID") is not None:
        raw["PATIENT_FOLLOWUP"] = {
            "GUID_APPOINTMENT": row.get("FollowupAppointmentGUID"),
            "GUID_PATIENT": row.get("FollowupPatientGUID"),
            "CheckInDate": row.get("FollowupCheckInDate"),
            "CheckInDelay": row.get("FollowupCheckInDelay"),
            "CheckInTime": row.get("FollowupCheckInTime"),
            "CheckOutDelay": row.get("FollowupCheckOutDelay"),
            "CheckOutTime": row.get("FollowupCheckOutTime"),
            "AdministrationTimeSpent": row.get("FollowupAdministrationTimeSpent"),
            "TreatmentTimeSpent": row.get("FollowupTreatmentTimeSpent"),
            "WaitingRoomTimeSpent": row.get("FollowupWaitingRoomTimeSpent"),
            "TotalDelay": row.get("FollowupTotalDelay"),
            "TotalTimeSpent": row.get("FollowupTotalTimeSpent"),
        }

    return CanonicalAppointment(
        **canonical_envelope(context, "appointment", source_id, raw),
        patient_uuid=patient_uuid,
        center_uuid=center_uuid,
        professional_uuid=professional_uuid,
        chair_uuid=chair_uuid,
        status_uuid=status_uuid,
        scheduled_date=appointment_date,
        scheduled_time=start_time,
        duration_minutes=duration,
        notes=notes,
        coarse_status=coarse_status,
        tenant_label=context.tenant_label,
    )


def _appointment_start(date_value: Any, start_value: Any) -> tuple[date | None, time | None]:
    actual_date = _as_date(date_value)
    actual_time = _as_time(start_value)
    if actual_date is None and isinstance(start_value, datetime):
        actual_date = start_value.date()
    return actual_date, actual_time


def _duration_minutes(
    appointment_date: date,
    start_time: time,
    end_value: Any,
) -> int | None:
    end_time = _as_time(end_value)
    if end_time is None:
        return None
    start = datetime.combine(appointment_date, start_time)
    end = datetime.combine(appointment_date, end_time)
    if end < start:
        end += timedelta(days=1)
    if end == start:
        return None
    seconds = (end - start).total_seconds()
    return int(seconds // 60)


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _as_time(value: Any) -> time | None:
    if isinstance(value, datetime):
        return value.time().replace(tzinfo=None)
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    return None


def _default_center_uuid(context: TransformContext) -> UUID | None:
    if len(context.center_source_ids) != 1:
        return None
    return context.id_mapping.resolve(
        context.source_system,
        "center",
        context.center_source_ids[0],
        require_known=True,
    )


def _coarse_status(label: str | None) -> AppointmentStatus:
    if label is None:
        return AppointmentStatus.UNKNOWN
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode().lower()
    normalized = " ".join(normalized.replace("_", " ").replace("-", " ").split())
    if normalized in {"scheduled", "pending", "pendiente", "programada", "programado"}:
        return AppointmentStatus.SCHEDULED
    if normalized in {"confirmed", "confirmada", "confirmado"}:
        return AppointmentStatus.CONFIRMED
    if normalized in {"attended", "atendida", "atendido", "realizada", "realizado", "completed"}:
        return AppointmentStatus.ATTENDED
    if normalized in {"no show", "no presentada", "no presentado", "ausente"}:
        return AppointmentStatus.NO_SHOW
    if normalized in {"cancelled", "canceled", "cancelada", "cancelado", "anulada"}:
        return AppointmentStatus.CANCELLED
    return AppointmentStatus.UNKNOWN
