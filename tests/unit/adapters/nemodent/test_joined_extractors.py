"""Joined extractors use fixed projections and preserve source table fields."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.nemodent.extractors import (
    applied_treatments,
    appointments,
)


class _Cursor:
    def __init__(self, row: tuple[Any, ...]) -> None:
        self._rows = [row]
        self.query = ""
        self.closed = False

    def execute(self, query: str) -> _Cursor:
        self.query = query
        return self

    def fetchmany(self, _size: int) -> list[tuple[Any, ...]]:
        rows = self._rows
        self._rows = []
        return rows

    def close(self) -> None:
        self.closed = True


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _Cursor:
        return self._cursor


def test_appointment_join_is_streamed_with_slot_staff_columns() -> None:
    cursor = _Cursor(tuple(range(len(appointments._RESULT_COLUMNS))))
    rows = list(appointments.iter_joined_rows(_Connection(cursor)))  # type: ignore[arg-type]

    assert len(rows) == 1
    assert tuple(rows[0]) == appointments._RESULT_COLUMNS
    assert "[APPOINTMENT_SLOTS]" in cursor.query
    assert "[APPOINTMENT_SLOT_PERSONNEL]" in cursor.query
    assert "[PATIENT_FOLLOWUP]" in cursor.query
    assert cursor.closed


def test_applied_treatment_join_preserves_history_and_task_projections() -> None:
    cursor = _Cursor(tuple(range(len(applied_treatments._RESULT_COLUMNS))))
    rows = list(applied_treatments.iter_joined_rows(_Connection(cursor)))  # type: ignore[arg-type]

    assert len(rows) == 1
    assert tuple(rows[0]) == applied_treatments._RESULT_COLUMNS
    assert "[PATIENT_PROCEDURES]" in cursor.query
    assert "[PATIENT_HISTORY]" in cursor.query
    assert "LEFT JOIN [PATIENT_HISTORY]" in cursor.query
    assert "[PATIENT_TASKS]" in cursor.query
    assert cursor.closed
