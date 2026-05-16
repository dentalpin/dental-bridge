"""Tests for the self-FK validation pass."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.patient import CanonicalPatient
from dental_bridge.core.dpmf.writer import DpmfWriter
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.self_fk import validate_and_nullify_orphans

_TS = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _patient(source_id: str, *, referrer: str | None = None) -> CanonicalPatient:
    referrer_uuid = derive_canonical_uuid("gesden", "patient", referrer) if referrer else None
    return CanonicalPatient(
        canonical_uuid=derive_canonical_uuid("gesden", "patient", source_id),
        source_system="gesden",
        source_id=source_id,
        adapter_version="0.0.1",
        extracted_at=_TS,
        raw_source_data={"IdPac": int(source_id)},
        sex=Sex.UNKNOWN,
        referrer_patient_uuid=referrer_uuid,
    )


def _write(path: Path, patients: list[CanonicalPatient]) -> None:
    with DpmfWriter(
        path,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="x",
    ) as w:
        for p in patients:
            w.append(p)
        w.record_entity_count("patient", len(patients))


def test_orphan_self_fk_is_nullified_and_warned(tmp_path: Path) -> None:
    out = tmp_path / "out.dpm"
    # Patient 2 references patient 99, which is NOT emitted.
    _write(out, [_patient("1"), _patient("2", referrer="99")])

    warnings = WarningRegistry()
    with sqlite3.connect(out) as conn:
        cleaned = validate_and_nullify_orphans(conn, warnings)
    assert cleaned == 1

    # The payload of patient 2 must no longer contain the orphan reference.
    with sqlite3.connect(out) as conn:
        row = conn.execute("SELECT payload FROM patient WHERE source_id = '2'").fetchone()
    payload = json.loads(row[0])
    assert payload["referrer_patient_uuid"] is None

    codes = [w.code for w in warnings]
    assert "patient.referrer_patient_uuid.orphan" in codes


def test_valid_self_fk_is_preserved(tmp_path: Path) -> None:
    out = tmp_path / "out.dpm"
    # Patient 2 references patient 1, which IS emitted.
    _write(out, [_patient("1"), _patient("2", referrer="1")])

    warnings = WarningRegistry()
    with sqlite3.connect(out) as conn:
        cleaned = validate_and_nullify_orphans(conn, warnings)
    assert cleaned == 0
    assert len(warnings) == 0

    expected = str(derive_canonical_uuid("gesden", "patient", "1"))
    with sqlite3.connect(out) as conn:
        row = conn.execute("SELECT payload FROM patient WHERE source_id = '2'").fetchone()
    payload = json.loads(row[0])
    assert payload["referrer_patient_uuid"] == expected
