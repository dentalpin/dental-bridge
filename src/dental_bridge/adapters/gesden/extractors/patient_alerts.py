"""Read patient alerts from ``AlertPac``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    a.Id,
    a.IdPac,
    a.IdCentro,
    a.NumAlerta,
    a.Texto,
    a.Marcado,
    a.Guid_Tenant
FROM AlertPac a
ORDER BY a.Id
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
