"""End-to-end test of the runner's checkpoint integration."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dental_bridge.core.adapters.origin_abc import OriginAdapter
from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import (
    BaseCanonicalEntity,
    derive_canonical_uuid,
)
from dental_bridge.core.canonical.patient import CanonicalPatient
from dental_bridge.core.dpmf.writer import DpmfWriter
from dental_bridge.core.pipeline.checkpoint import InMemoryCheckpointStore
from dental_bridge.core.pipeline.runner import run_extraction

_TS = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class _StubAdapter(OriginAdapter):
    name = "gesden"
    version = "0.0.1"

    def __init__(self, source_ids: list[str]) -> None:
        self._source_ids = list(source_ids)

    def connect(self, dsn: str, **kwargs: object) -> None:
        return None

    def fingerprint(self) -> str:
        return "sha256:stub"

    def supported_entities(self) -> list[str]:
        return ["patient"]

    def default_entity_order(self) -> list[str]:
        return ["patient"]

    def iter_entity(self, entity_type: str) -> Iterator[BaseCanonicalEntity]:
        if entity_type != "patient":
            raise KeyError(entity_type)
        for sid in self._source_ids:
            yield CanonicalPatient(
                canonical_uuid=derive_canonical_uuid("gesden", "patient", sid),
                source_system="gesden",
                source_id=sid,
                adapter_version=self.version,
                extracted_at=_TS,
                raw_source_data={"IdPac": int(sid)},
                sex=Sex.UNKNOWN,
            )

    def close(self) -> None:
        return None


def test_runner_requires_run_id_with_checkpoint(tmp_path: Path) -> None:
    adapter = _StubAdapter(["1"])
    store = InMemoryCheckpointStore()
    out = tmp_path / "x.dpm"
    with (
        DpmfWriter(
            out,
            source_system="gesden",
            source_adapter_version="0.0.1",
            exporter_version="0.0.1",
            tenant_label="x",
        ) as writer,
        pytest.raises(ValueError),
    ):
        run_extraction(
            adapter,
            writer,
            entity_order=["patient"],
            checkpoint=store,
            show_progress=False,
        )


def test_runner_skips_already_emitted_rows(tmp_path: Path) -> None:
    out_a = tmp_path / "a.dpm"
    out_b = tmp_path / "b.dpm"
    store = InMemoryCheckpointStore()
    run_id = "test-run"

    # First run: emit two patients.
    adapter_a = _StubAdapter(["1", "2"])
    with DpmfWriter(
        out_a,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="x",
    ) as writer:
        run_extraction(
            adapter_a,
            writer,
            entity_order=["patient"],
            checkpoint=store,
            run_id=run_id,
            show_progress=False,
        )

    assert store.count_emitted(run_id, "patient") == 2

    # Second run with same store + run_id: the adapter sees the same source
    # rows, but the runner should skip them and emit none to the new file.
    adapter_b = _StubAdapter(["1", "2", "3"])
    with DpmfWriter(
        out_b,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="x",
    ) as writer:
        run_extraction(
            adapter_b,
            writer,
            entity_order=["patient"],
            checkpoint=store,
            run_id=run_id,
            show_progress=False,
        )

    # Only patient "3" was new, so file B should hold a single row.
    with sqlite3.connect(out_b) as conn:
        count = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    assert count == 1
    assert store.count_emitted(run_id, "patient") == 3
