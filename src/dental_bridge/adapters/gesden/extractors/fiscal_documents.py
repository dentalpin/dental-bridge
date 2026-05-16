"""Read fiscal documents from ``DocAdmin``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.Ident,
    d.Doc,
    d.Serie,
    d.NumDoc,
    d.Anyo,
    d.IdEmisor,
    d.IdSerieOficial,
    d.SerieOficial,
    d.NumDocOficial,
    d.TipoDocumento,
    d.TipoFactura,
    d.FecDoc,
    d.IdCli,
    d.IdCliTutor,
    d.IdUser,
    d.Nombre,
    d.Apellidos,
    d.RazonSocial,
    d.NIF,
    d.NIFTutor,
    d.Direccion,
    d.CP,
    d.IdMotivo,
    d.IdDocAdminOrigen,
    d.ConceptoG,
    d.Modelo,
    d.Abonado,
    d.Abono,
    d.Anulacion,
    d.Hash,
    d.HashControl,
    d.CodigoATCUD,
    d.CodigoQR,
    d.NumTransaccion,
    d.IdDevolucionTransaccion,
    d._origen,
    d.Guid_Tenant
FROM DocAdmin d
ORDER BY d.Ident
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
