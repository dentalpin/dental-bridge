"""Compute a stable hash describing the shape of a Gesdén database.

Two Gesdén installations with the same fingerprint can be migrated with
the same adapter version. A new fingerprint means either a newer Gesdén
build, a clinic-specific customisation, or an unrelated database — in any
case the adapter should refuse to proceed without explicit registration.

The fingerprint is computed over user tables only: ``sys.tables`` rows
filtered out of the system schema, joined with ``sys.columns`` for column
names, types and nullability. We deliberately ignore: default values
(often clinic-specific), indexes (frequently rebuilt), object IDs (vary
across attaches), comments and extended properties.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyodbc

_FINGERPRINT_QUERY = """
SELECT
    t.name        AS table_name,
    c.column_id   AS column_id,
    c.name        AS column_name,
    ty.name       AS type_name,
    c.max_length  AS max_length,
    c.precision   AS precision,
    c.scale       AS scale,
    c.is_nullable AS is_nullable
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types  ty ON ty.user_type_id = c.user_type_id
WHERE t.is_ms_shipped = 0
ORDER BY t.name, c.column_id
"""


def compute_fingerprint(conn: pyodbc.Connection) -> str:
    """Return ``sha256:<hex>`` describing the schema shape."""
    cursor = conn.cursor()
    rows = cursor.execute(_FINGERPRINT_QUERY).fetchall()
    hasher = hashlib.sha256()
    for row in rows:
        line = (
            f"{row.table_name}|{row.column_id}|{row.column_name}|"
            f"{row.type_name}|{row.max_length}|{row.precision}|{row.scale}|"
            f"{int(row.is_nullable)}\n"
        )
        hasher.update(line.encode("utf-8"))
    return "sha256:" + hasher.hexdigest()
