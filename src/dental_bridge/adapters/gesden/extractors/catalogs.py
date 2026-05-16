"""Generic extractor for Gesdén lookup tables.

Each catalog specification maps one Gesdén table to a CanonicalCatalogItem
``kind``. The extractor reads the table and yields rows that the
transformer turns into canonical entries. New catalogs are added by
appending a :class:`CatalogSpec` to :data:`CATALOG_SPECS` — no new
extractor or transformer module is needed per catalog.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts
from dental_bridge.core.canonical.catalog_item import CatalogKind

if TYPE_CHECKING:
    import pyodbc


@dataclass(slots=True, frozen=True)
class CatalogSpec:
    """How one Gesdén catalog table maps to a CanonicalCatalogItem ``kind``."""

    kind: CatalogKind
    table: str
    pk_column: str
    code_column: str | None = "Codigo"
    name_column: str | None = "Descripcio"
    parent_column: str | None = None
    # Some catalogs have alternative description columns we want preserved.
    description_column: str | None = None
    where_clause: str | None = None


# Order is intentional but does not encode dependencies — those are handled
# by the topological runner. Within this list, parent catalogs appear
# before their dependants so that hierarchical FKs can be deterministically
# derived even when the runner emits items one by one.
# Column shapes verified against an actual Gesdén SOURCE_DB database.
# Notes on naming variance observed:
# - Most tables spell the label column "Descripcio" (no trailing n).
# - A few (TBoxes, TRRecall, IconoTratAgenda) use "Descripcion".
# - Most lookups have NO short code at all; the few that do use their own
#   column name (Tipo, CodigoOMC, CodPro, CodINE, IsoAlfa2, Codigo).
CATALOG_SPECS: tuple[CatalogSpec, ...] = (
    CatalogSpec(CatalogKind.COUNTRY, "TPaises", "IdPais", code_column="IsoAlfa2"),
    CatalogSpec(
        CatalogKind.PROVINCE,
        "TProvin",
        "IdProvin",
        code_column="CodPro",
        parent_column="IdPais",
    ),
    CatalogSpec(
        CatalogKind.CITY,
        "TPoblaci",
        "IdPoblacio",
        code_column="CodINE",
        parent_column="IdProvin",
    ),
    CatalogSpec(CatalogKind.CIVIL_STATUS, "TECivil", "IdECivil", code_column=None),
    CatalogSpec(CatalogKind.TITLE, "TTrato", "IdTrato", code_column=None),
    CatalogSpec(CatalogKind.PROFESSION, "TProfesi", "IdProfesio", code_column=None),
    CatalogSpec(CatalogKind.SPECIALTY, "TEspecOMC", "IdTipoEspec", code_column="CodigoOMC"),
    CatalogSpec(
        CatalogKind.REFERRAL_SOURCE,
        "TRefer",
        "IdRef",
        code_column="Codigo",
        name_column="Origen",
        description_column="Destino",
    ),
    CatalogSpec(CatalogKind.PAYMENT_METHOD, "TForPago", "IdForPago", code_column="Tipo"),
    CatalogSpec(CatalogKind.BANK, "Bancos", "IdBanco", code_column=None),
    CatalogSpec(CatalogKind.APPOINTMENT_STATUS, "TSitCita", "IdSitC", code_column=None),
    CatalogSpec(CatalogKind.CHAIR, "TBoxes", "IdBox", code_column=None, name_column="Descripcion"),
    CatalogSpec(CatalogKind.RECALL_REASON, "TMRecall", "IdMotivo", code_column=None),
    CatalogSpec(
        CatalogKind.RECALL_OUTCOME,
        "TRRecall",
        "IdTRRecall",
        code_column=None,
        name_column="Descripcion",
    ),
    CatalogSpec(
        CatalogKind.ICON,
        "IconoTratAgenda",
        "IdIcono",
        code_column=None,
        name_column="Descripcion",
    ),
)


SPECS_BY_KIND: dict[CatalogKind, CatalogSpec] = {spec.kind: spec for spec in CATALOG_SPECS}


def iter_rows(conn: pyodbc.Connection, spec: CatalogSpec) -> Iterator[dict[str, Any]]:
    """Stream rows for a single catalog table according to ``spec``."""
    columns = [spec.pk_column]
    if spec.code_column:
        columns.append(spec.code_column)
    if spec.name_column:
        columns.append(spec.name_column)
    if spec.parent_column:
        columns.append(spec.parent_column)
    if spec.description_column and spec.description_column not in columns:
        columns.append(spec.description_column)

    where = f" WHERE {spec.where_clause}" if spec.where_clause else ""
    query = f"SELECT {', '.join(columns)} FROM {spec.table}{where} ORDER BY {spec.pk_column}"

    cursor = conn.cursor()
    cursor.execute(query)
    yield from iter_dicts(cursor)
