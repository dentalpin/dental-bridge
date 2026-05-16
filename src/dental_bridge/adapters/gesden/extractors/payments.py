"""Read client payments from ``PagoCli``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    p.IdPagoCli,
    p.IdCli,
    p.IdCentro,
    p.IdBanco,
    p.IdForPago,
    p.IdUser,
    p.IdAnulado,
    p.IdPagoCliRelacionado,
    p.IdentTM,
    p.IdMotivo,
    p.Pagado,
    p.FecPago,
    p.Tipo,
    p.NRecibo,
    p.NumIngre,
    p.NCPago,
    p.NFactura,
    p.CodIBAN,
    p.NumTransaccion,
    p.IdDevolucionTransaccion,
    p.IdPasarelaPago,
    p.IdRemesaBancaria,
    p.Automatico,
    p.NoDisponible,
    p.Guid_Tenant
FROM PagoCli p
ORDER BY p.IdPagoCli
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
