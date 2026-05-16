"""Read budget lines from ``PresuTto``."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    l.Ident,
    l.Id_Presu,
    l.IdPac,
    l.NumSerie,
    l.NumPre,
    l.LinPre,
    l.IdTto,
    l.IdTratamiento,
    l.IdTtoMedOrig,
    l.IdCol,
    l.IdColAux,
    l.IdCli,
    l.Orden,
    l.StaTto,
    l.Unidades,
    l.ImportePre,
    l.ImporteUni,
    l.Dto,
    l.ImporteDto,
    l.BaseImponible,
    l.IdTipoIVA,
    l.TpcIVA,
    l.ImporteIVA,
    l.FecIni,
    l.FecFin,
    l.FecAcepta,
    l.Notas,
    l.Tiempo,
    l.ZonasBoca,
    l.PiezasAdu,
    l.PiezasLec,
    l.PiezasNum,
    l.ZonasPieza,
    l.IdTipoOdg,
    l.Cuadrantes,
    l.Arcadas,
    l.DespX,
    l.DespY,
    l.Rotacion,
    l.Guid_Tenant
FROM PresuTto l
ORDER BY l.Ident
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
