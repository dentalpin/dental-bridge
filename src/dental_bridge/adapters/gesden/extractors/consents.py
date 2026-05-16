"""Read signed consents from ``TConsinCab``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    c.IdConsin,
    c.IdPac,
    c.IdUsu,
    c.IdCol,
    c.FirmaIdUsu,
    c.IdColFirma,
    c.Titulo,
    c.Representante,
    c.Doctor,
    c.NumColegiado,
    c.Texto,
    c.Html,
    c.FechaGen,
    c.FechaFirma,
    c.NumImp,
    c.Firmado
FROM TConsinCab c
ORDER BY c.IdConsin
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
