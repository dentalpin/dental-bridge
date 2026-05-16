"""Tests that the reference-validation pass handles cross-table FKs.

An appointment may reference an appointment_recurrence that is not in
the extraction scope. The validator should NULL the reference and emit
a warning, exactly like for same-table self-FKs.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from dental_bridge.core.canonical.appointment import (
    AppointmentStatus,
    CanonicalAppointment,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.dpmf.writer import DpmfWriter
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.self_fk import validate_and_nullify_orphans

_TS = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _appointment(source_id: str, *, recurrence: str | None) -> CanonicalAppointment:
    rec_uuid = (
        derive_canonical_uuid("gesden", "appointment_recurrence", recurrence)
        if recurrence
        else None
    )
    return CanonicalAppointment(
        canonical_uuid=derive_canonical_uuid("gesden", "appointment", source_id),
        source_system="gesden",
        source_id=source_id,
        adapter_version="0.0.1",
        extracted_at=_TS,
        raw_source_data={"IdCita": int(source_id)},
        recurrence_uuid=rec_uuid,
        coarse_status=AppointmentStatus.UNKNOWN,
    )


def test_orphan_cross_fk_is_nullified(tmp_path: Path) -> None:
    out = tmp_path / "out.dpm"
    with DpmfWriter(
        out,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="x",
    ) as w:
        w.append(_appointment("1", recurrence="99"))  # 99 not emitted
        w.record_entity_count("appointment", 1)

    warnings = WarningRegistry()
    with sqlite3.connect(out) as conn:
        cleaned = validate_and_nullify_orphans(conn, warnings)
    assert cleaned == 1

    with sqlite3.connect(out) as conn:
        payload = json.loads(conn.execute("SELECT payload FROM appointment").fetchone()[0])
    assert payload["recurrence_uuid"] is None

    codes = [w.code for w in warnings]
    assert any(c.startswith("appointment.recurrence_uuid") for c in codes)
