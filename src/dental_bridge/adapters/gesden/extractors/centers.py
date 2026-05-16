"""Read centres (clinics/sites) from the Gesdén ``Centros`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    c.IdCentro,
    c.CodCentro,
    c.Descripcio
FROM Centros c
WHERE c.IdCentro >= 0
ORDER BY c.IdCentro
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
