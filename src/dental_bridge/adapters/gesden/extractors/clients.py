"""Read client (payer) rows from the Gesdén ``Clientes`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc

_QUERY = """
SELECT
    c.IdCli,
    c.Nombre,
    c.Apellidos,
    c.RazonSocial,
    c.NIF,
    c.Email,
    c.Tel1,
    c.Tel2,
    c.TelMovil,
    c.Fax,
    c.Direccion,
    c.CP,
    c.IdPoblacio,
    c.Mailing,
    c.IdCentro,
    c.IdCIA,
    c.Guid_Tenant
FROM Clientes c
ORDER BY c.IdCli
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
