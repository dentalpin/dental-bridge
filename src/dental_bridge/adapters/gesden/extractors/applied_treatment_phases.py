"""Read applied-treatment phases from ``TtosMedFases``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    f.IdTtosMedFase,
    f.IdTtosMed,
    f.IdTratamientoFase,
    f.IdCol,
    f.IdColAux,
    f.NumFase,
    f.Estado,
    f.Fecha,
    f.TpcFacturar,
    f.Notas,
    f.Guid_Tenant
FROM TtosMedFases f
ORDER BY f.IdTtosMedFase
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
