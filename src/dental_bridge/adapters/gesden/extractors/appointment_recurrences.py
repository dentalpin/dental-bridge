"""Read recurring-appointment series headers from ``DCitasPeriod``.

Real column shape observed against SOURCE_DB:

- IdCitasP (PK)
- FechaInicio / FechaFinal (datetime)
- Texto (description)
- Frecuencia / Periodicidad
- DiaSem / DiaMes / Mes (per-cadence parameters)
- NumeroCitas
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    p.IdCitasP,
    p.FechaInicio,
    p.FechaFinal,
    p.Texto,
    p.Frecuencia,
    p.Periodicidad,
    p.DiaSem,
    p.DiaMes,
    p.Mes,
    p.NumeroCitas
FROM DCitasPeriod p
ORDER BY p.IdCitasP
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
