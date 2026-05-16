"""Read day-slot rows from the Gesdén ``TCalDias`` table.

Real shape (verified against SOURCE_DB):

- IdCal, IdDia, IdUsu, IdSit

``IdDia`` is a weekday code (1..7), not a date. The row associates a
user and a situation with each weekday of a calendar.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.IdCal,
    d.IdDia,
    d.IdUsu,
    d.IdSit
FROM TCalDias d
ORDER BY d.IdCal, d.IdDia, d.IdUsu
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
