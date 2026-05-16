"""Read per-tariff treatment variants from ``Tratamientos_Tarifas``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    v.IdTratamientoTarifa,
    v.IdTratamiento,
    v.IdTarifa,
    v.CodTto,
    v.IdTipoEspec,
    v.IdGrupo,
    v.Inactivo,
    v.Guid_Tenant
FROM Tratamientos_Tarifas v
ORDER BY v.IdTratamientoTarifa
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
