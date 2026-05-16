"""Canonical appointment and appointment-recurrence entities."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class AppointmentStatus(StrEnum):
    """Coarse status taxonomy.

    Source PMSs carry richer per-clinic status codes; the original
    ``IdSitC`` is preserved as ``raw_source_data`` and the canonical
    catalog entry for that status is referenced via ``status_uuid``. The
    enum below collapses the most common cases for importers that need a
    quick decision.
    """

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    ATTENDED = "attended"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class CanonicalAppointment(BaseCanonicalEntity):
    """A single clinical appointment slot."""

    entity_type: str = Field(default="appointment", frozen=True)

    patient_uuid: UUID | None = None
    client_uuid: UUID | None = None
    center_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    chair_uuid: UUID | None = Field(
        default=None,
        description="Canonical catalog_item UUID of the chair/box (TBoxes).",
    )
    status_uuid: UUID | None = Field(
        default=None,
        description="Canonical catalog_item UUID of the appointment status (TSitCita).",
    )

    recurrence_uuid: UUID | None = Field(
        default=None,
        description=(
            "Reference to the AppointmentRecurrence parent when this slot is part of a series."
        ),
    )

    scheduled_date: date | None = Field(
        default=None,
        description="Civil date the appointment is scheduled for.",
    )
    scheduled_time: time | None = Field(
        default=None,
        description="Local clock-time the appointment starts at.",
    )
    duration_minutes: int | None = None

    notes: str | None = None
    coarse_status: AppointmentStatus = AppointmentStatus.UNKNOWN

    created_at: datetime | None = None

    tenant_label: str | None = None


class CanonicalAppointmentRecurrence(BaseCanonicalEntity):
    """Series-parent record for recurring appointments."""

    entity_type: str = Field(default="appointment_recurrence", frozen=True)

    description: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    weekly_cadence: int | None = Field(
        default=None,
        description="Repeat every N weeks. Null when the source carries a different cadence.",
    )

    tenant_label: str | None = None
