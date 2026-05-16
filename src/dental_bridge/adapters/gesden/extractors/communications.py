"""Read communication runs from ``EdMail``.

Per-recipient detail rows (``EdMailL``) are intentionally not exported
in v0.1: the table has no stable single-column PK and the value of each
recipient row is reconstructible from the run header plus the patient
filter. We capture the run headers only.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    m.IdRun,
    m.IdUser,
    m.IdCentro,
    m.IdDoc,
    m.FecPrintI,
    m.FecPrintF,
    m.Notas,
    m.Filtro
FROM EdMail m
ORDER BY m.IdRun
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
