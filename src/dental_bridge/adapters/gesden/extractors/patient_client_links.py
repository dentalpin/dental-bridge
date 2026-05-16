"""Read the M:N patient↔client relation from the Gesdén ``PacCli`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc

_QUERY = """
SELECT
    pc.IdPac,
    pc.IdCli,
    pc.Poliza,
    pc.FecAlta,
    pc.FecCaduc,
    pc.Inactivo
FROM PacCli pc
ORDER BY pc.IdPac, pc.IdCli
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
