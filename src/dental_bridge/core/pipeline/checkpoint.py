"""Local checkpoint store for resumable extractions.

A run that is interrupted (network blip, machine shutdown, the operator
hit Ctrl-C) should be re-runnable without redoing already-emitted rows.
This module persists the set of ``(run_id, entity_type, source_id)``
triples that the runner has successfully written to the DPMF file.

Sprint 2 ships an SQLite-backed implementation. The base class lets
future code (in-memory for tests, a remote store for hosted scenarios)
plug in without touching the runner.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_data_dir

_DEFAULT_NAME = "state.db"


def _default_state_path() -> Path:
    """Return the platform-appropriate path for the checkpoint database.

    Windows:  ``%APPDATA%\\dental-bridge\\state.db``
    macOS:    ``~/Library/Application Support/dental-bridge/state.db``
    Linux:    ``~/.local/share/dental-bridge/state.db``

    Falls back to ``./.dental-bridge/state.db`` when the OS-specific
    directory cannot be created (e.g. read-only home in a container).
    """
    try:
        base = Path(user_data_dir(appname="dental-bridge", appauthor=False))
        base.mkdir(parents=True, exist_ok=True)
        return base / _DEFAULT_NAME
    except OSError:
        fallback = Path(".dental-bridge")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback / _DEFAULT_NAME


class CheckpointStore(ABC):
    """Persistent record of what has already been emitted in a given run."""

    @abstractmethod
    def mark_emitted(self, run_id: str, entity_type: str, source_id: str) -> None:
        """Record one ``source_id`` as written for ``run_id``/``entity_type``."""

    @abstractmethod
    def is_emitted(self, run_id: str, entity_type: str, source_id: str) -> bool:
        """Return ``True`` if this triple has already been recorded."""

    @abstractmethod
    def count_emitted(self, run_id: str, entity_type: str) -> int:
        """How many rows have already been emitted for this entity in this run."""

    @abstractmethod
    def close(self) -> None:
        """Release any resources held by the store."""


class InMemoryCheckpointStore(CheckpointStore):
    """Useful in tests; never crosses process boundaries."""

    def __init__(self) -> None:
        self._seen: set[tuple[str, str, str]] = set()

    def mark_emitted(self, run_id: str, entity_type: str, source_id: str) -> None:
        self._seen.add((run_id, entity_type, source_id))

    def is_emitted(self, run_id: str, entity_type: str, source_id: str) -> bool:
        return (run_id, entity_type, source_id) in self._seen

    def count_emitted(self, run_id: str, entity_type: str) -> int:
        return sum(1 for key in self._seen if key[0] == run_id and key[1] == entity_type)

    def close(self) -> None:
        return None


class SqliteCheckpointStore(CheckpointStore):
    """SQLite-backed checkpoint, suitable for production use on a workstation."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else _default_state_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emitted (
                run_id      TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                source_id   TEXT NOT NULL,
                emitted_at  TEXT NOT NULL,
                PRIMARY KEY (run_id, entity_type, source_id)
            )
            """
        )
        self._conn.commit()

    def mark_emitted(self, run_id: str, entity_type: str, source_id: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO emitted (run_id, entity_type, source_id, emitted_at) "
            "VALUES (?, ?, ?, ?)",
            (run_id, entity_type, source_id, datetime.now(UTC).isoformat()),
        )
        self._conn.commit()

    def is_emitted(self, run_id: str, entity_type: str, source_id: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM emitted WHERE run_id = ? AND entity_type = ? AND source_id = ?",
            (run_id, entity_type, source_id),
        )
        return cur.fetchone() is not None

    def count_emitted(self, run_id: str, entity_type: str) -> int:
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM emitted WHERE run_id = ? AND entity_type = ?",
            (run_id, entity_type),
        )
        return int(cur.fetchone()[0])

    def reset(self, run_id: str) -> None:
        """Drop all checkpoint state for ``run_id``. Useful for re-runs."""
        self._conn.execute("DELETE FROM emitted WHERE run_id = ?", (run_id,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def default_run_id(*, tenant_label: str, source_fingerprint: str | None) -> str:
    """Derive a stable run identifier from extract parameters.

    Two invocations with the same ``tenant_label`` and source schema
    fingerprint share a run_id, so re-running the CLI against the same
    clinic resumes rather than restarting.
    """
    fp = (source_fingerprint or "unknown").replace(":", "_")
    return f"{tenant_label}@{fp}"
