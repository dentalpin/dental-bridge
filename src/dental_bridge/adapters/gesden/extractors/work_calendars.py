"""Read work-calendar headers from the Gesdén ``TCalCa`` table.

Real column shape observed against a Gesdén SOURCE_DB database:

- IdCal (PK)
- Descripcio
- Inactivo (flag, not a date)
- IdCentro
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    c.IdCal,
    c.Descripcio,
    c.Inactivo,
    c.IdCentro
FROM TCalCa c
ORDER BY c.IdCal
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
