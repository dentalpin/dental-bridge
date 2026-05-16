"""Read attached patient documents from ``TDocumentosPac``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    d.IdDocPac,
    d.IdPac,
    d.IdUsu,
    d.FirmaIdUsu,
    d.FechaDoc,
    d.FechaIns,
    d.Descripcion,
    d.Notas,
    d.Original,
    d.TipoDoc,
    d.Firmado,
    d.Guid_Tenant
FROM TDocumentosPac d
ORDER BY d.IdDocPac
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
