"""Read appointment rows from the Gesdén ``DCitas`` table.

The real primary key of DCitas is the composite ``(IdUsu, IdOrden)`` —
``IdCita`` is a secondary identifier added later and is not unique
across rows. The extractor selects both so the transformer can produce
a composite ``source_id`` and avoid collapsing distinct rows.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
-- ``DCitas.IdUsu`` points at TUsuAgd (the agenda column / slot owner)
-- and is populated on virtually every row, while ``DCitas.IdCol`` (the
-- explicit per-appointment colaborador) is sparse in real exports
-- (~3% in field data). We left-join TUsuAgd to recover the colaborador
-- linked to the agenda column itself (``OwnerIdCol``); the transformer
-- uses that as the primary professional reference and falls back to
-- the agenda-user keying (``usuagd:<IdUsu>``) only when both
-- ``DCitas.IdCol`` and ``TUsuAgd.IdCol`` are null.
--
-- Many real exports leave ``TUsuAgd.IdCol`` empty even on agenda columns
-- that obviously belong to a TColabos colaborador (the operator never
-- linked them). We fuzz-match those orphans by name and use the
-- resolved IdCol as a secondary fallback so appointment ownership
-- routes to the real practitioner instead of a synthetic agenda-only
-- profile. Two-tier match (CodExt then Descripcio) and a uniqueness
-- guard (``HAVING COUNT(DISTINCT t.IdCol) = 1``) keep the merge safe.
WITH orphan_stripped AS (
    SELECT IdUsu,
        UPPER(LTRIM(RTRIM(Descripcio))) AS desc_u,
        UPPER(LTRIM(RTRIM(REPLACE(REPLACE(Descripcio, 'DRA.', ''), 'DR.', '')))) AS desc_clean,
        UPPER(LTRIM(RTRIM(CodExt))) AS code_u
    FROM TUsuAgd
    WHERE IdCol IS NULL
),
orphan_match_codext AS (
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
    SELECT IdUsu, resolved_idcol FROM orphan_match_codext
    UNION ALL
    SELECT IdUsu, resolved_idcol FROM orphan_match_desc
)
SELECT
    d.IdUsu,
    d.IdOrden,
    d.IdCita,
    d.IdPac,
    d.IdCli,
    d.IdCentro,
    d.IdCol,
    COALESCE(u.IdCol, r.resolved_idcol) AS OwnerIdCol,
    d.IdSitC,
    d.IdBox,
    d.Fecha,
    d.Hora,
    d.Duracion,
    d.Texto,
    d.IdCitasP,
    d.FecAlta
FROM DCitas d
LEFT JOIN TUsuAgd u ON u.IdUsu = d.IdUsu
LEFT JOIN orphan_resolve r ON r.IdUsu = d.IdUsu
ORDER BY d.IdUsu, d.IdOrden
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
