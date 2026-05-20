"""Read professionals from the Gesdén ``TColabos`` + ``TUsuAgd`` tables.

Why two tables: in Gesdén a ``TColabos`` row is a "collaborator" (a
dentist, hygienist or auxiliary the clinic does business with),
whereas a ``TUsuAgd`` row is an agenda *column* — the
schedulable resource that owns appointment slots. ``DCitas.IdUsu``
points at ``TUsuAgd.IdUsu`` (NOT at ``TColabos.IdCol``), and that
linkage is what receptionists actually use day to day.

Many real clinics never fill ``TUsuAgd.IdCol``, so the two tables
overlap only partially. We emit a canonical ``professional`` for every
``TColabos`` row **and** for every ``TUsuAgd`` row that isn't already
covered by a ``TColabos.IdCol`` reference — that way every
``DCitas.IdUsu`` value resolves downstream. ``source_id`` is suffixed
with ``usuagd:`` for the TUsuAgd path so canonical UUIDs stay
collision-free.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    'tcolabos' AS source_table,
    CAST(p.IdCol AS NVARCHAR(50)) AS pk,
    p.Codigo,
    p.Nombre,
    p.Apellidos,
    p.NIF,
    p.IdTipoColab
FROM TColabos p
UNION ALL
SELECT
    'tusuagd' AS source_table,
    'usuagd:' + CAST(u.IdUsu AS NVARCHAR(50)) AS pk,
    NULL AS Codigo,
    NULL AS Nombre,
    u.Descripcio AS Apellidos,  -- TUsuAgd carries a single label
                                -- (often a surname, sometimes a first
                                -- name or "DRA. SURNAME"). Routing it
                                -- to Apellidos makes the destination
                                -- user show as "Profesional <label>"
                                -- which is the closest match for
                                -- Spanish dental clinic conventions.
    NULL AS NIF,
    NULL AS IdTipoColab
FROM TUsuAgd u
WHERE u.IdCol IS NULL  -- skip if already represented in TColabos
ORDER BY pk
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
