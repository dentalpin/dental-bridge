"""Read appointment rows from the Gesdén ``DCitas`` table.

The real primary key of DCitas is the composite ``(IdUsu, IdOrden)`` —
``IdCita`` is a secondary identifier added later and is not unique
across rows. The extractor selects both so the transformer can produce
a composite ``source_id`` and avoid collapsing distinct rows.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.IdUsu,
    d.IdOrden,
    d.IdCita,
    d.IdPac,
    d.IdCli,
    d.IdCentro,
    d.IdCol,
    d.IdSitC,
    d.IdBox,
    d.Fecha,
    d.Hora,
    d.Duracion,
    d.Texto,
    d.IdCitasP,
    d.FecAlta
FROM DCitas d
ORDER BY d.IdUsu, d.IdOrden
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
