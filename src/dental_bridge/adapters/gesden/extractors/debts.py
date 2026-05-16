"""Read debts from ``DeudaCli``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.IdDeudaCli,
    d.IdCli,
    d.IdPac,
    d.IdCentro,
    d.IdentTM,
    d.IdAnulado,
    d.IdMotivoIncobrable,
    d.NumTto,
    d.NumFase,
    d.FecPlazo,
    d.Adeudo,
    d.Pendiente,
    d.Liquidado,
    d.Incobrable,
    d.DescMotivoIncobrable,
    d.Docs,
    d.NFactura,
    d.NNotaTto,
    d.Modalidad,
    d.Guid_Tenant
FROM DeudaCli d
ORDER BY d.IdDeudaCli
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
