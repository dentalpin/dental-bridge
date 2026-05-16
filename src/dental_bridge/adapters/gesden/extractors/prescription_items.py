"""Read prescribed-drug detail rows from ``RecetasDet``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.IdRecetaDet,
    d.IdReceta,
    d.IdPac,
    d.IdTrat,
    d.DescFarmaco,
    d.Pauta,
    d.Posologia,
    d.Unidades,
    d.Envases,
    d.Duracion,
    d.OrdenDisp,
    d.DispPrev,
    d.Guid_Tenant
FROM RecetasDet d
ORDER BY d.IdRecetaDet
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
