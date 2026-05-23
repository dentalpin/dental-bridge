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
WITH orphan_stripped AS (
    -- Normalise the agenda-column label for fuzzy matching. ``Descripcio``
    -- often carries a "DRA. " or "DR. " honorific that does not appear on
    -- ``TColabos.Apellidos`` — strip it before comparing.
    SELECT IdUsu,
        UPPER(LTRIM(RTRIM(Descripcio))) AS desc_u,
        UPPER(LTRIM(RTRIM(REPLACE(REPLACE(Descripcio, 'DRA.', ''), 'DR.', '')))) AS desc_clean,
        UPPER(LTRIM(RTRIM(CodExt))) AS code_u
    FROM TUsuAgd
    WHERE IdCol IS NULL
),
orphan_match_codext AS (
    -- Priority 1: CodExt (the agenda column's short identifier) usually
    -- maps to a token inside ``TColabos.Apellidos``. Match only when a
    -- single TColabos comes out so we never silently fuse two distinct
    -- colaboradores into one.
    SELECT s.IdUsu, MIN(t.IdCol) AS resolved_idcol
    FROM orphan_stripped s
    JOIN TColabos t ON t.Activo = 'S' AND LEN(s.code_u) >= 4 AND (
        UPPER(LTRIM(RTRIM(t.Apellidos))) = s.code_u
        OR UPPER(LTRIM(RTRIM(t.Apellidos))) LIKE s.code_u + ' %'
        OR UPPER(LTRIM(RTRIM(t.Apellidos))) LIKE '% ' + s.code_u
    )
    GROUP BY s.IdUsu
    HAVING COUNT(DISTINCT t.IdCol) = 1
),
orphan_match_desc AS (
    -- Priority 2: Descripcio token match against Apellidos / Nombre.
    -- Skip orphans already resolved via CodExt.
    SELECT s.IdUsu, MIN(t.IdCol) AS resolved_idcol
    FROM orphan_stripped s
    JOIN TColabos t ON t.Activo = 'S' AND (
        UPPER(LTRIM(RTRIM(t.Apellidos))) = s.desc_u
        OR UPPER(LTRIM(RTRIM(t.Apellidos))) = s.desc_clean
        OR UPPER(LTRIM(RTRIM(t.Apellidos))) LIKE s.desc_clean + ' %'
        OR UPPER(LTRIM(RTRIM(t.Nombre))) = s.desc_u
        OR UPPER(LTRIM(RTRIM(t.Nombre))) = s.desc_clean
    )
    WHERE s.IdUsu NOT IN (SELECT IdUsu FROM orphan_match_codext)
    GROUP BY s.IdUsu
    HAVING COUNT(DISTINCT t.IdCol) = 1
),
orphan_resolve AS (
    -- Orphan rows that map cleanly back to a single TColabos. Skipped
    -- from the professional UNION so we don't emit a duplicate canonical
    -- entity, and used by the appointments extractor to attribute
    -- ``DCitas.IdUsu`` to the real colaborador.
    SELECT IdUsu, resolved_idcol FROM orphan_match_codext
    UNION ALL
    SELECT IdUsu, resolved_idcol FROM orphan_match_desc
),
activity_col AS (
    -- Latest clinical trace per TColabos.IdCol. Uses smalldatetime/datetime
    -- columns directly; DCitas.Fecha is a Gesdén-encoded int so we fall back
    -- to DCitas.FecAlta (row-insert timestamp), which is good enough for
    -- "did this professional generate any traffic in the last N months".
    --
    -- Appointments bridge: DCitas.IdCol is populated on only ~3 % of rows in
    -- the field; the real owner sits on DCitas.IdUsu → TUsuAgd.IdCol. We
    -- count both so a colaborador who only owns work through an agenda
    -- column does not look "inactive" downstream.
    SELECT IdCol, MAX(act) AS last_activity_at FROM (
        SELECT IdCol,        FecIni    AS act FROM TtosMed  WHERE IdCol IS NOT NULL AND FecIni    IS NOT NULL
        UNION ALL
        SELECT IdCol,        FecPresup AS act FROM Presu    WHERE IdCol IS NOT NULL AND FecPresup IS NOT NULL
        UNION ALL
        SELECT IdCol,        Fecha     AS act FROM Recalls  WHERE IdCol IS NOT NULL AND Fecha     IS NOT NULL
        UNION ALL
        SELECT IdCol,        FecAlta   AS act FROM DCitas   WHERE IdCol IS NOT NULL AND FecAlta   IS NOT NULL
        UNION ALL
        SELECT u.IdCol,      c.FecAlta AS act
        FROM DCitas c
        JOIN TUsuAgd u ON u.IdUsu = c.IdUsu
        WHERE u.IdCol IS NOT NULL AND c.FecAlta IS NOT NULL
        UNION ALL
        -- Bridge via the orphan-resolution CTE: appointments owned by a
        -- TUsuAgd row whose IdCol is null but which fuzzy-matched a real
        -- TColabos. Without this branch the matched colaborador would
        -- still look "inactive" downstream because no appointment row
        -- references their IdCol directly.
        SELECT r.resolved_idcol, c.FecAlta AS act
        FROM DCitas c
        JOIN orphan_resolve r ON r.IdUsu = c.IdUsu
        WHERE c.FecAlta IS NOT NULL
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
  AND u.IdUsu NOT IN (SELECT IdUsu FROM orphan_resolve)  -- skip fuzzy-matched orphans
ORDER BY pk
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
