"""Read applied-treatment rows from ``TtosMed``.

Columns are scoped to the canonical fields plus the odontogram-encoding
columns we preserve verbatim. Legacy ``Edu10..Edu24`` and other
clinic-specific ``Comodin*`` columns are skipped.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    t.Ident,
    t.IdPac,
    t.NumTto,
    t.IdTto,
    t.IdCol,
    t.IdColAux,
    t.IdCli,
    t.IdUser,
    t.IdCentro,
    t.IdPresuTto,
    t.IdRef,
    t.IdTipoEspec,
    t.NumDocUnico,
    t.NumTransaccion,
    t.StaTto,
    t.FecIni,
    t.FecFin,
    t.FechaCaduc,
    t.FechaValida,
    t.Importe,
    t.Dto,
    t.ImporteDto,
    t.Pendiente,
    t.ImportePrivado,
    t.ImporteMutua,
    t.Actos,
    t.Tiempo,
    t.SesRealiz,
    t.Notas,
    t.ZonasBoca,
    t.PiezasAdu,
    t.PiezasLec,
    t.PiezasNum,
    t.ZonasPieza,
    t.IdTipoOdg,
    t.Cuadrantes,
    t.Arcadas,
    t.DespX,
    t.DespY,
    t.Rotacion,
    t.Guid_Tenant
FROM TtosMed t
ORDER BY t.Ident
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
