"""Read scheduled patient recalls from ``Recalls``.

The real primary key of ``Recalls`` is the composite ``(IdPac, NumRec)``;
there is also a surrogate ``Id`` column but it does not constrain
uniqueness in the catalogue. The transformer uses the composite.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    r.Id,
    r.IdPac,
    r.NumRec,
    r.IdCol,
    r.IdColRevisa,
    r.IdCentro,
    r.IdMotivo,
    r.IdResultado,
    r.IdEstado,
    r.Id_Presu,
    r.Id_TtosMed,
    r.IdRecallOrigen,
    r.Fecha,
    r.FechaContacto,
    r.Telefono,
    r.Carta,
    r.EMail,
    r.SMS,
    r.Asistido,
    r.Citado,
    r.Comentario,
    r.Observaciones,
    r.Guid_Tenant
FROM Recalls r
ORDER BY r.IdPac, r.NumRec
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
