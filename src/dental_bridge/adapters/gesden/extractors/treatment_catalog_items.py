"""Read treatment catalog rows from the Gesdén ``Tratamientos`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    t.IdTratamiento,
    t.Codigo,
    t.DescripMed,
    t.DescripPac,
    t.DescripAgd,
    t.IdTipoEspec,
    t.IdTipoODG,
    t.Duracion,
    t.NumFases,
    t.PrecioReferencia,
    t.Inactivo,
    t.Desde,
    t.Hasta,
    t.Guid_Tenant
FROM Tratamientos t
ORDER BY t.IdTratamiento
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
