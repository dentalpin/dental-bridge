"""Read budget headers from ``Presu``.

The natural PK observed in this schema is ``(IdPac, NumPre)`` but the
``Ident`` surrogate identity column is unique and is what child tables
reference (``PresuTto.Id_Presu``), so we use it as the canonical
``source_id``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    p.Ident,
    p.IdPac,
    p.NumSerie,
    p.NumPre,
    p.Titulo,
    p.Notas,
    p.FecPresup,
    p.FecAcepta,
    p.FecRechaz,
    p.ObsRechaz,
    p.IdCol,
    p.IdCentro,
    p.IdUserElabora,
    p.IdUserPresentacion,
    p.Estado,
    p.EsAlternativa,
    p.AlternativaDe,
    p.Id_PresuOriginal,
    p.Id_UserRechaz,
    p.Hash,
    p.HashControl,
    p.CodigoATCUD,
    p.CodigoQR,
    p.Guid_Tenant
FROM Presu p
ORDER BY p.Ident
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
