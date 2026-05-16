"""DDL for the DPMF SQLite container.

Tables defined here mirror the layout documented in ``spec/dpmf-v0.1.md``.
Per-entity tables are created on first append; see :mod:`writer`.
"""

from __future__ import annotations

FORMAT_VERSION = "0.1.0"
USER_VERSION = 1  # PRAGMA user_version, the format's MAJOR

META_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

ENTITIES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _entities (
    entity_type    TEXT PRIMARY KEY,
    row_count      INTEGER NOT NULL,
    schema_version TEXT NOT NULL
)
"""

FILES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _files (
    canonical_uuid         TEXT PRIMARY KEY,
    parent_entity_type     TEXT NOT NULL,
    parent_canonical_uuid  TEXT NOT NULL,
    relative_path          TEXT NOT NULL,
    declared_size_bytes    INTEGER,
    sha256                 TEXT,
    mime_hint              TEXT
)
"""

FILES_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_files_parent
    ON _files(parent_entity_type, parent_canonical_uuid)
"""

WARNINGS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS _warnings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    source_id   TEXT,
    severity    TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
    code        TEXT NOT NULL,
    message     TEXT NOT NULL,
    raw_data    TEXT CHECK (raw_data IS NULL OR json_valid(raw_data))
)
"""

ENTITY_TABLE_DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS "{entity_type}" (
    canonical_uuid   TEXT PRIMARY KEY,
    source_id        TEXT NOT NULL,
    source_system    TEXT NOT NULL,
    payload          TEXT NOT NULL CHECK (json_valid(payload)),
    raw_source_data  TEXT NOT NULL CHECK (json_valid(raw_source_data)),
    extracted_at     TEXT NOT NULL
)
"""

ENTITY_INDEX_DDL_TEMPLATE = """
CREATE INDEX IF NOT EXISTS "idx_{entity_type}_source"
    ON "{entity_type}"(source_system, source_id)
"""

# Per-entity SemVer. Bumped independently of the format itself when a
# canonical entity's field set changes. Importers read this from _entities.
ENTITY_SCHEMA_VERSIONS: dict[str, str] = {
    "patient": "0.1.0",
    "client": "0.1.0",
    "patient_client_link": "0.1.0",
    "center": "0.1.0",
    "professional": "0.1.0",
    "user": "0.1.0",
    "catalog_item": "0.1.0",
    "work_calendar": "0.1.0",
    "work_calendar_day": "0.1.0",
    "work_calendar_shift": "0.1.0",
    "appointment_recurrence": "0.1.0",
    "appointment": "0.1.0",
    "treatment_catalog_item": "0.1.0",
    "treatment_catalog_variant": "0.1.0",
    "treatment_phase_template": "0.1.0",
    "applied_treatment": "0.1.0",
    "applied_treatment_phase": "0.1.0",
    "budget": "0.1.0",
    "budget_line": "0.1.0",
    "debt": "0.1.0",
    "payment": "0.1.0",
    "debt_payment_application": "0.1.0",
    "fiscal_document": "0.1.0",
    "fiscal_document_line": "0.1.0",
    "pharmacological_history": "0.1.0",
    "prescription": "0.1.0",
    "prescription_item": "0.1.0",
    "consent": "0.1.0",
    "patient_document": "0.1.0",
    "recall": "0.1.0",
    "patient_alert": "0.1.0",
    "communication": "0.1.0",
}
