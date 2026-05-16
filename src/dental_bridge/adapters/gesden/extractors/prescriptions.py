"""Read prescription headers from ``RecetasCab``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    r.IdRecetaIdent,
    r.IdPac,
    r.IdUsu,
    r.IdCol,
    r.IdCentro,
    r.Fecha,
    r.FecIns,
    r.FechaImpresion,
    r.Descripcio,
    r.Notas,
    r.NotasFarmaceutico,
    r.Diagnostico,
    r.TipoReceta,
    r.CVE,
    r.Dispensada,
    r.NumImpresiones,
    r.Anulada,
    r.Publico,
    r.Guid_Tenant
FROM RecetasCab r
ORDER BY r.IdRecetaIdent
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
