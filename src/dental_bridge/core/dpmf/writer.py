"""DPMF writer — Sprint 1 baseline.

Produces an uncompressed, unencrypted SQLite container with the layout
specified in ``spec/dpmf-v0.1.md``. Compression (zstd) and encryption
(AES-256-GCM) layers will wrap the output in Sprint 8.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from dental_bridge.core.canonical.base import BaseCanonicalEntity
from dental_bridge.core.dpmf.schema import (
    ENTITIES_TABLE_DDL,
    ENTITY_INDEX_DDL_TEMPLATE,
    ENTITY_SCHEMA_VERSIONS,
    ENTITY_TABLE_DDL_TEMPLATE,
    FILES_INDEX_DDL,
    FILES_TABLE_DDL,
    FORMAT_VERSION,
    META_TABLE_DDL,
    USER_VERSION,
    WARNINGS_TABLE_DDL,
)
from dental_bridge.core.pipeline.errors import WarningRecord

_INTEGRITY_PLACEHOLDER = "PENDING"


class DpmfWriter:
    """Builds a DPMF file row by row.

    Usage::

        with DpmfWriter(path, source_system="gesden",
                        source_adapter_version="0.0.1",
                        exporter_version="0.0.1",
                        tenant_label="clinica-x") as w:
            for entity in adapter.iter_entity("patient"):
                w.append(entity)
            w.record_entity_count("patient", n)
    """

    def __init__(
        self,
        path: Path,
        *,
        source_system: str,
        source_adapter_version: str,
        exporter_version: str,
        tenant_label: str,
        source_schema_fingerprint: str | None = None,
    ) -> None:
        self.path = Path(path)
        self._known_entity_tables: set[str] = set()
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA foreign_keys = OFF")
        self._conn.execute(f"PRAGMA user_version = {USER_VERSION}")
        self._initialise_schema()
        self._write_meta(
            source_system=source_system,
            source_adapter_version=source_adapter_version,
            exporter_version=exporter_version,
            tenant_label=tenant_label,
            source_schema_fingerprint=source_schema_fingerprint,
        )

    # Context manager -----------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                self.finalise()
        finally:
            self._conn.close()

    # Public API ----------------------------------------------------------
    def append(self, entity: BaseCanonicalEntity) -> None:
        table = entity.entity_type
        self._ensure_entity_table(table)
        payload = entity.model_dump_json()
        raw = json.dumps(entity.raw_source_data, default=_json_default, ensure_ascii=False)
        self._conn.execute(
            f'INSERT OR REPLACE INTO "{table}" '
            f"(canonical_uuid, source_id, source_system, payload, raw_source_data, extracted_at) "
            f"VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(entity.canonical_uuid),
                entity.source_id,
                entity.source_system,
                payload,
                raw,
                entity.extracted_at.astimezone(UTC).isoformat(),
            ),
        )

    def record_entity_count(self, entity_type: str, count: int) -> None:
        # Every _entities entry requires a physical table, even at row_count=0.
        # Readers discover entity tables from this index.
        self._ensure_entity_table(entity_type)
        version = ENTITY_SCHEMA_VERSIONS.get(entity_type, "0.1.0")
        self._conn.execute(
            "INSERT OR REPLACE INTO _entities (entity_type, row_count, schema_version) "
            "VALUES (?, ?, ?)",
            (entity_type, count, version),
        )

    def append_warning(self, warning: WarningRecord) -> None:
        raw = (
            json.dumps(warning.raw_data, default=_json_default, ensure_ascii=False)
            if warning.raw_data is not None
            else None
        )
        self._conn.execute(
            "INSERT INTO _warnings "
            "(entity_type, source_id, severity, code, message, raw_data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                warning.entity_type,
                warning.source_id,
                warning.severity,
                warning.code,
                warning.message,
                raw,
            ),
        )

    def append_file_ref(
        self,
        *,
        canonical_uuid: str,
        parent_entity_type: str,
        parent_canonical_uuid: str,
        relative_path: str,
        declared_size_bytes: int | None = None,
        sha256: str | None = None,
        mime_hint: str | None = None,
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO _files "
            "(canonical_uuid, parent_entity_type, parent_canonical_uuid, "
            " relative_path, declared_size_bytes, sha256, mime_hint) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                canonical_uuid,
                parent_entity_type,
                parent_canonical_uuid,
                relative_path,
                declared_size_bytes,
                sha256,
                mime_hint,
            ),
        )

    def finalise(self) -> str:
        """Commit, compute integrity hash and store it. Returns the digest.

        The integrity hash is computed over the *logical content* of the
        DPMF — every entity row's canonical fields and every warning — in
        a deterministic order. We avoid hashing the raw SQLite bytes
        because SQLite does not guarantee a byte-for-byte stable file for
        a given logical state (page layout depends on insertion order,
        rowid choices, etc.). A logical hash is what an importer needs
        anyway: "did the payload survive transport unchanged?".
        """
        self._conn.commit()
        digest = self._compute_logical_hash()
        self._conn.execute(
            "UPDATE _meta SET value = ? WHERE key = 'integrity_hash'",
            (digest,),
        )
        self._conn.commit()
        return digest

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the underlying connection for post-pass mutations.

        Used by self-FK validation and other late stages that need to
        rewrite payload JSON in place. Do not use for direct schema
        changes — those belong in this module.
        """
        return self._conn

    def _compute_logical_hash(self) -> str:
        hasher = hashlib.sha256()
        # _entities — sorted to be order-independent.
        for row in self._conn.execute(
            "SELECT entity_type, row_count, schema_version FROM _entities ORDER BY entity_type"
        ):
            hasher.update(f"_entities|{row[0]}|{row[1]}|{row[2]}\n".encode())
        # Each entity table — content rows in canonical_uuid order.
        for entity_type in sorted(self._known_entity_tables):
            for row in self._conn.execute(
                f"SELECT canonical_uuid, source_id, source_system, payload, raw_source_data "
                f'FROM "{entity_type}" ORDER BY canonical_uuid'
            ):
                hasher.update(
                    f"{entity_type}|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}\n".encode()
                )
        # _files — sorted.
        for row in self._conn.execute(
            "SELECT canonical_uuid, parent_entity_type, parent_canonical_uuid, "
            "relative_path, declared_size_bytes, sha256, mime_hint "
            "FROM _files ORDER BY canonical_uuid"
        ):
            hasher.update(("_files|" + "|".join(str(v) for v in row) + "\n").encode("utf-8"))
        # _warnings — autoincrement id is insertion order; preserve that.
        for row in self._conn.execute(
            "SELECT id, entity_type, source_id, severity, code, message, raw_data "
            "FROM _warnings ORDER BY id"
        ):
            hasher.update(("_warnings|" + "|".join(str(v) for v in row) + "\n").encode("utf-8"))
        return hasher.hexdigest()

    # Internal ------------------------------------------------------------
    def _initialise_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute(META_TABLE_DDL)
        cursor.execute(ENTITIES_TABLE_DDL)
        cursor.execute(FILES_TABLE_DDL)
        cursor.execute(FILES_INDEX_DDL)
        cursor.execute(WARNINGS_TABLE_DDL)
        self._conn.commit()

    def _write_meta(
        self,
        *,
        source_system: str,
        source_adapter_version: str,
        exporter_version: str,
        tenant_label: str,
        source_schema_fingerprint: str | None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        items = {
            "format_version": FORMAT_VERSION,
            "source_system": source_system,
            "source_adapter_version": source_adapter_version,
            "source_schema_fingerprint": source_schema_fingerprint or "",
            "exporter_tool": "dental-bridge",
            "exporter_version": exporter_version,
            "exported_at": now,
            "tenant_label": tenant_label,
            "integrity_hash_algo": "sha256",
            "integrity_hash": _INTEGRITY_PLACEHOLDER,
        }
        self._conn.executemany(
            "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
            items.items(),
        )
        self._conn.commit()

    def _ensure_entity_table(self, entity_type: str) -> None:
        if entity_type in self._known_entity_tables:
            return
        if not _is_safe_identifier(entity_type):
            raise ValueError(f"unsafe entity_type identifier: {entity_type!r}")
        cursor = self._conn.cursor()
        cursor.execute(ENTITY_TABLE_DDL_TEMPLATE.format(entity_type=entity_type))
        cursor.execute(ENTITY_INDEX_DDL_TEMPLATE.format(entity_type=entity_type))
        self._conn.commit()
        self._known_entity_tables.add(entity_type)


def _json_default(value: object) -> object:
    """Coerce types Pydantic/sqlite3 won't serialise natively.

    Kept minimal — we want to surface unexpected types as errors rather than
    silently dropping them.
    """
    from datetime import date
    from datetime import datetime as _dt
    from decimal import Decimal
    from uuid import UUID as _UUID

    if isinstance(value, _UUID):
        return str(value)
    if isinstance(value, _dt | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    raise TypeError(f"unsupported JSON type: {type(value).__name__}")


def _is_safe_identifier(name: str) -> bool:
    """Allow lower_snake_case identifiers only — table names are interpolated into SQL."""
    if not name:
        return False
    return all(ch.islower() or ch.isdigit() or ch == "_" for ch in name) and name[0].isalpha()
