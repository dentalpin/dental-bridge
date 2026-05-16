"""Read patient rows from the Gesdén ``Pacientes`` table."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc

# Explicit column list. We never SELECT * — that would couple our pipeline
# to incidental columns clinics may have added through Gesdén plugins.
# Columns kept here come from `docs/schema_map.md` and the observed schema.
_QUERY = """
SELECT
    p.IdPac,
    p.NumPac,
    p.Nombre,
    p.Apellidos,
    p.NIF,
    p.FecNacim,
    p.FecAlta,
    p.Sexo,
    p.Inactivo,
    p.Exitus,
    p.AceptaLOPD,
    p.IdCli,
    p.IdCliTutor,
    p.IdCliPac,
    p.IdCliDefec,
    p.IdCol,
    p.IdCentro,
    p.IdPacReferidor,
    p.Guid_Tenant
FROM Pacientes p
ORDER BY p.IdPac
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
