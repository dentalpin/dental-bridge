"""Tests for the appointment-recurrence transformer."""

from __future__ import annotations

from datetime import date

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.appointment_recurrences import transform
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def test_recurrence_basic_mapping() -> None:
    row = {
        "IdCitasP": 7,
        "FechaInicio": date(2026, 1, 1),
        "FechaFinal": date(2026, 6, 30),
        "Texto": "Ortodoncia mensual",
        "Frecuencia": 4,
        "Periodicidad": 0,
        "DiaSem": 1,
        "DiaMes": 0,
        "Mes": 0,
        "NumeroCitas": 6,
    }
    r = transform(row, _ctx())
    assert r.starts_on == date(2026, 1, 1)
    assert r.ends_on == date(2026, 6, 30)
    assert r.weekly_cadence == 4
    assert r.description == "Ortodoncia mensual"
