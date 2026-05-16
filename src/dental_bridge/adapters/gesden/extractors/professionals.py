"""Read professionals from the Gesdén ``TColabos`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    p.IdCol,
    p.Codigo,
    p.Nombre,
    p.Apellidos,
    p.NIF,
    p.IdTipoColab
FROM TColabos p
ORDER BY p.IdCol
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
