"""Read fiscal-document lines from ``LinAdmin``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


# Note: LinAdmin's column is ``identTM`` (lowercase d in 'ident') — the
# Gesdén schema is inconsistent about casing across tables.
_QUERY = """
SELECT
    l.IdLinAdmin,
    l.IdDocAdmin,
    l.IdDeudaCli,
    l.IdPagoCli,
    l.IdDeudaPago,
    l.IdPac,
    l.identTM,
    l.NumLinea,
    l.Concepto,
    l.Importe,
    l.BaseImponible,
    l.IdTipoIVA,
    l.TpcIVA,
    l.ImporteIVA,
    l.Dto,
    l.ImporteDto,
    l.Actos,
    l.Abonado,
    l.Abono,
    l.Guid_Tenant
FROM LinAdmin l
ORDER BY l.IdLinAdmin
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
