"""Read debt-payment applications from ``DeudaPago``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    a.IdDeudaPago,
    a.IdDeudaCli,
    a.IdPagoCli,
    a.IdDocAdminDeuda,
    a.Pagado,
    a.FecPago,
    a.FecExpoCP,
    a.EditTtos,
    a.SubTipoPago,
    a.Guid_Tenant
FROM DeudaPago a
ORDER BY a.IdDeudaPago
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
