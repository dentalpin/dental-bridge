"""Read recurring weekday shifts from the Gesdén ``TCalHor`` table.

Real shape (verified against SOURCE_DB):

- IdCal, IdDia, HIni, HFin, AOOnLine

``HIni``/``HFin`` are minutes-since-midnight, ``IdDia`` is weekday 1..7.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    h.IdCal,
    h.IdDia,
    h.HIni,
    h.HFin,
    h.AOOnLine
FROM TCalHor h
ORDER BY h.IdCal, h.IdDia, h.HIni
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
