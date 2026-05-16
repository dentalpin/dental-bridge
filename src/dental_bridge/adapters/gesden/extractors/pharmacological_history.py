"""Read patient pharmacological-history rows from ``TTratamientos``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    t.IdPac,
    t.IdTrat,
    t.IdFarmaco,
    t.IdUsu,
    t.IdCentro,
    t.IdTipoEspec,
    t.DescFarmaco,
    t.Dosificacion,
    t.Dosis,
    t.ViaAdmin,
    t.Frecuencia,
    t.Observac,
    t.Fecha,
    t.FecIns,
    t.FecFin,
    t.Tipo,
    t.Publico,
    t.Guid_Tenant
FROM TTratamientos t
ORDER BY t.IdPac, t.IdTrat
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
