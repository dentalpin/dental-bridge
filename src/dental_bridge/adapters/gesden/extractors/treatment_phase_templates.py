"""Read treatment-phase templates from ``TratamientosFases``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    f.IdTratamientoFase,
    f.IdTratamiento,
    f.DescripMed,
    f.Observaciones,
    f.Duracion,
    f.TpcFacturar,
    f.OrdenEjecucion,
    f.MinDias,
    f.MaxDias,
    f.Guid_Tenant
FROM TratamientosFases f
ORDER BY f.IdTratamientoFase
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
