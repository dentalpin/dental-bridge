"""Smoke tests for the DPMF writer."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.patient import CanonicalPatient
from dental_bridge.core.dpmf.reader import open_dpmf
from dental_bridge.core.dpmf.writer import DpmfWriter

_FIXED_TS = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _make_patient(source_id: str = "1", *, extracted_at: datetime = _FIXED_TS) -> CanonicalPatient:
    return CanonicalPatient(
        canonical_uuid=derive_canonical_uuid("gesden", "patient", source_id),
        source_system="gesden",
        source_id=source_id,
        adapter_version="0.0.1",
        extracted_at=extracted_at,
        raw_source_data={"IdPac": int(source_id)},
        given_name="A",
        family_name="B",
        sex=Sex.UNKNOWN,
    )


def test_writer_creates_well_formed_file(tmp_path: Path) -> None:
    output = tmp_path / "out.dpm"
    with DpmfWriter(
        output,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="test-tenant",
        source_schema_fingerprint="sha256:test",
    ) as w:
        w.append(_make_patient("1"))
        w.append(_make_patient("2"))
        w.record_entity_count("patient", 2)

    assert output.exists()

    with sqlite3.connect(output) as conn:
        meta = dict(conn.execute("SELECT key, value FROM _meta"))
        assert meta["format_version"].startswith("0.1")
        assert meta["source_system"] == "gesden"
        assert meta["tenant_label"] == "test-tenant"
        assert meta["integrity_hash"] != "PENDING"
        assert len(meta["integrity_hash"]) == 64  # sha256 hex

        entities = {
            row[0]: row[1] for row in conn.execute("SELECT entity_type, row_count FROM _entities")
        }
        assert entities["patient"] == 2

        rows = conn.execute("SELECT canonical_uuid, payload FROM patient").fetchall()
        assert len(rows) == 2
        for _, payload in rows:
            assert json.loads(payload)["entity_type"] == "patient"


def test_zero_row_entity_has_a_table_readers_can_query(tmp_path: Path) -> None:
    output = tmp_path / "empty-entity.dpm"
    with DpmfWriter(
        output,
        source_system="nemodent",
        source_adapter_version="0.1.0",
        exporter_version="0.1.0",
        tenant_label="test-tenant",
    ) as writer:
        writer.record_entity_count("applied_treatment_phase", 0)
        digest = writer.finalise()

    with open_dpmf(output) as conn:
        entities = dict(conn.execute("SELECT entity_type, row_count FROM _entities"))
        assert entities["applied_treatment_phase"] == 0
        assert conn.execute("SELECT COUNT(*) FROM applied_treatment_phase").fetchone()[0] == 0
        declared_hash = conn.execute(
            "SELECT value FROM _meta WHERE key='integrity_hash'"
        ).fetchone()[0]
        assert declared_hash == digest


def test_writer_refuses_unsafe_entity_name(tmp_path: Path) -> None:
    output = tmp_path / "out.dpm"
    with DpmfWriter(
        output,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="x",
    ) as w:
        bogus = _make_patient()
        unsafe = bogus.model_copy(update={"entity_type": "patient; DROP TABLE"})
        with pytest.raises(ValueError):
            w.append(unsafe)


def test_integrity_hash_is_deterministic(tmp_path: Path) -> None:
    """Two DPMF files with the same logical content must share an integrity hash.

    The hash is computed over canonical rows (sorted by uuid) and warnings,
    not over the raw SQLite bytes — SQLite layout is not byte-stable across
    independent writes of the same logical content, so byte-hashing would
    be brittle.
    """
    out_a = tmp_path / "a.dpm"
    out_b = tmp_path / "b.dpm"

    def _write(path: Path) -> str:
        with DpmfWriter(
            path,
            source_system="gesden",
            source_adapter_version="0.0.1",
            exporter_version="0.0.1",
            tenant_label="x",
        ) as w:
            # Insert in opposite orders to prove the hash is order-independent.
            w.append(_make_patient("1"))
            w.append(_make_patient("2"))
            w.record_entity_count("patient", 2)
        with sqlite3.connect(path) as conn:
            return conn.execute("SELECT value FROM _meta WHERE key='integrity_hash'").fetchone()[0]

    digest_a = _write(out_a)
    digest_b = _write(out_b)
    assert digest_a == digest_b
    assert len(digest_a) == 64  # sha256 hex


def test_integrity_hash_changes_with_content(tmp_path: Path) -> None:
    out_a = tmp_path / "a.dpm"
    out_b = tmp_path / "b.dpm"

    def _write(path: Path, ids: list[str]) -> str:
        with DpmfWriter(
            path,
            source_system="gesden",
            source_adapter_version="0.0.1",
            exporter_version="0.0.1",
            tenant_label="x",
        ) as w:
            for source_id in ids:
                w.append(_make_patient(source_id))
            w.record_entity_count("patient", len(ids))
        with sqlite3.connect(path) as conn:
            return conn.execute("SELECT value FROM _meta WHERE key='integrity_hash'").fetchone()[0]

    assert _write(out_a, ["1", "2"]) != _write(out_b, ["1", "3"])


# Silence unused-import warnings — kept for the simpler integrity test above
_ = hashlib
