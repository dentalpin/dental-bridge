"""Tests for the work-calendar family of transformers."""

from __future__ import annotations

from datetime import time

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.work_calendar_days import (
    transform as transform_day,
)
from dental_bridge.adapters.gesden.transformers.work_calendar_shifts import (
    transform as transform_shift,
)
from dental_bridge.adapters.gesden.transformers.work_calendars import (
    transform as transform_calendar,
)
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


def test_calendar_header() -> None:
    row = {
        "IdCal": 1,
        "Descripcio": "Horario general",
        "Inactivo": 0,
        "IdCentro": 1,
    }
    c = transform_calendar(row, _ctx())
    assert c.name == "Horario general"
    assert c.center_uuid == derive_canonical_uuid("gesden", "center", "1")
    assert c.code is None
    assert c.chair_uuid is None


def test_calendar_day_composite_key() -> None:
    row = {"IdCal": 1, "IdDia": 3, "IdUsu": 7, "IdSit": 2}
    d = transform_day(row, _ctx())
    assert d.source_id == "1:3:7"
    assert d.calendar_uuid == derive_canonical_uuid("gesden", "work_calendar", "1")
    # Day is intentionally None — IdDia is a weekday, not a date.
    assert d.day is None


def test_calendar_shift_decodes_times() -> None:
    row = {
        "IdCal": 1,
        "IdDia": 1,  # Monday
        "HIni": 32400,  # 09:00 in seconds-since-midnight
        "HFin": 46800,  # 13:00
        "AOOnLine": 0,
    }
    s = transform_shift(row, _ctx())
    assert s.weekday == 1
    assert s.start_time == time(9, 0)
    assert s.end_time == time(13, 0)


def test_calendar_shift_invalid_weekday_becomes_null() -> None:
    row = {"IdCal": 1, "IdDia": 99, "HIni": 0, "HFin": 60, "AOOnLine": 0}
    s = transform_shift(row, _ctx())
    assert s.weekday is None
