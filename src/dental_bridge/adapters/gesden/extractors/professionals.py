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
WITH activity_col AS (
    -- Latest clinical trace per TColabos.IdCol. Uses smalldatetime/datetime
    -- columns directly; DCitas.Fecha is a Gesdén-encoded int so we fall back
    -- to DCitas.FecAlta (row-insert timestamp), which is good enough for
    -- "did this professional generate any traffic in the last N months".
    SELECT IdCol, MAX(act) AS last_activity_at FROM (
        SELECT IdCol, FecIni    AS act FROM TtosMed  WHERE IdCol IS NOT NULL AND FecIni    IS NOT NULL
        UNION ALL
        SELECT IdCol, FecPresup AS act FROM Presu    WHERE IdCol IS NOT NULL AND FecPresup IS NOT NULL
        UNION ALL
        SELECT IdCol, Fecha     AS act FROM Recalls  WHERE IdCol IS NOT NULL AND Fecha     IS NOT NULL
        UNION ALL
        SELECT IdCol, FecAlta   AS act FROM DCitas   WHERE IdCol IS NOT NULL AND FecAlta   IS NOT NULL
    ) u
    GROUP BY IdCol
),
activity_usu AS (
    -- Latest clinical trace per TUsuAgd.IdUsu (agenda column). Only DCitas
    -- references IdUsu — TtosMed/Presu/Recalls do not.
    SELECT IdUsu, MAX(FecAlta) AS last_activity_at
    FROM DCitas
    WHERE IdUsu IS NOT NULL AND FecAlta IS NOT NULL
    GROUP BY IdUsu
)
SELECT
    'tcolabos' AS source_table,
    CAST(p.IdCol AS NVARCHAR(50)) AS pk,
    p.Codigo,
    p.Nombre,
    p.Apellidos,
    p.NIF,
    p.IdTipoColab,
    p.Activo,
    p.FecBaja,
    ac.last_activity_at AS LastActivityAt
FROM TColabos p
LEFT JOIN activity_col ac ON ac.IdCol = p.IdCol
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
    NULL AS IdTipoColab,
    -- TUsuAgd.Status: 1 = active agenda column, 0 = retired.
    -- Project to the TColabos 'Activo' char encoding so the transformer
    -- decodes both rows with the same helper.
    CASE WHEN u.Status = 0 THEN 'N' ELSE 'S' END AS Activo,
    NULL AS FecBaja,
    au.last_activity_at AS LastActivityAt
FROM TUsuAgd u
LEFT JOIN activity_usu au ON au.IdUsu = u.IdUsu
WHERE u.IdCol IS NULL  -- skip if already represented in TColabos
ORDER BY pk
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
