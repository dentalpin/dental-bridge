"""Canonical entities describing a clinic's working schedule.

Source PMSs typically split the schedule across three tables:

- a *header* per centre/box (``TCalCa`` in Gesdén),
- a list of *days* with overrides (``TCalDias``: holidays, custom hours),
- a list of *shifts* — the recurring weekly time bands (``TCalHor``).

To keep the canonical model simple and the mapping unambiguous, we emit
each source row as a distinct canonical entity. The destination importer
reconstructs the operational semantics it needs.
"""

from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalWorkCalendar(BaseCanonicalEntity):
    """A schedule definition that applies to a centre and optionally a chair."""

    entity_type: str = Field(default="work_calendar", frozen=True)

    name: str | None = None
    code: str | None = None
    center_uuid: UUID | None = None
    chair_uuid: UUID | None = None

    valid_from: date | None = None
    valid_until: date | None = None

    tenant_label: str | None = None


class CanonicalWorkCalendarDay(BaseCanonicalEntity):
    """A specific date's override for a work calendar.

    Used for public holidays, vacation closures or one-off custom hours.
    """

    entity_type: str = Field(default="work_calendar_day", frozen=True)

    calendar_uuid: UUID
    day: date | None = None
    is_working_day: bool | None = None
    notes: str | None = None


class CanonicalWorkCalendarShift(BaseCanonicalEntity):
    """A recurring time-of-day band within a calendar (e.g. 09:00-13:00 Mon-Fri)."""

    entity_type: str = Field(default="work_calendar_shift", frozen=True)

    calendar_uuid: UUID
    weekday: int | None = Field(
        default=None,
        description="ISO weekday number 1..7 (Mon=1, Sun=7), or None for daily.",
    )
    start_time: time | None = None
    end_time: time | None = None
