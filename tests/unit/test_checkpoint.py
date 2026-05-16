"""Tests for the checkpoint store."""

from __future__ import annotations

from pathlib import Path

from dental_bridge.core.pipeline.checkpoint import (
    InMemoryCheckpointStore,
    SqliteCheckpointStore,
    default_run_id,
)


def test_inmemory_roundtrip() -> None:
    store = InMemoryCheckpointStore()
    assert not store.is_emitted("r", "patient", "1")
    store.mark_emitted("r", "patient", "1")
    assert store.is_emitted("r", "patient", "1")
    assert store.count_emitted("r", "patient") == 1
    store.close()


def test_sqlite_persistence(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    store = SqliteCheckpointStore(db)
    store.mark_emitted("run-A", "patient", "42")
    store.mark_emitted("run-A", "patient", "43")
    store.mark_emitted("run-B", "patient", "42")
    store.close()

    store2 = SqliteCheckpointStore(db)
    assert store2.is_emitted("run-A", "patient", "42")
    assert store2.is_emitted("run-A", "patient", "43")
    assert not store2.is_emitted("run-A", "patient", "44")
    assert store2.is_emitted("run-B", "patient", "42")
    assert store2.count_emitted("run-A", "patient") == 2
    assert store2.count_emitted("run-B", "patient") == 1
    store2.close()


def test_sqlite_reset_clears_run(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    store = SqliteCheckpointStore(db)
    store.mark_emitted("run-A", "patient", "1")
    store.mark_emitted("run-B", "patient", "1")
    store.reset("run-A")
    assert not store.is_emitted("run-A", "patient", "1")
    assert store.is_emitted("run-B", "patient", "1")
    store.close()


def test_default_run_id_stable_across_calls() -> None:
    a = default_run_id(tenant_label="x", source_fingerprint="sha256:abc")
    b = default_run_id(tenant_label="x", source_fingerprint="sha256:abc")
    assert a == b
    c = default_run_id(tenant_label="x", source_fingerprint="sha256:other")
    assert a != c
