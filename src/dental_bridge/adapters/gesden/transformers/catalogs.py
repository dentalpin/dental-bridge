"""Transform any Gesdén lookup row into :class:`CanonicalCatalogItem`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.extractors.catalogs import CatalogSpec
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.catalog_item import CanonicalCatalogItem

# CatalogKind-internal entity_type — every kind produces rows under the
# single "catalog_item" entity, but its uuid namespace is qualified by
# kind to keep PKs unique across kinds.
_CATALOG_ENTITY = "catalog_item"


def transform(
    row: dict[str, Any], ctx: TransformContext, *, spec: CatalogSpec
) -> CanonicalCatalogItem:
    source_pk = row[spec.pk_column]
    source_id = f"{spec.kind.value}:{source_pk}"

    parent_uuid = None
    if spec.parent_column:
        parent_raw = row.get(spec.parent_column)
        if parent_raw not in (None, "", 0):
            parent_kind = _PARENT_KIND_OF.get(spec.kind)
            if parent_kind is not None:
                parent_uuid = derive_canonical_uuid(
                    ctx.source_system,
                    _CATALOG_ENTITY,
                    f"{parent_kind}:{parent_raw}",
                )

    code = normalise_string(row.get(spec.code_column)) if spec.code_column else None
    name = normalise_string(row.get(spec.name_column)) if spec.name_column else None
    description = (
        normalise_string(row.get(spec.description_column)) if spec.description_column else None
    )

    return CanonicalCatalogItem(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, _CATALOG_ENTITY, source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        kind=spec.kind,
        code=code,
        name=name,
        description=description,
        parent_uuid=parent_uuid,
    )


# Static parent-kind map. When a province carries IdPais, the parent
# canonical_uuid is derived under CatalogKind.COUNTRY. Same idea for cities.
_PARENT_KIND_OF: dict[Any, str] = {}


def _register_parent_links() -> None:
    """Populate _PARENT_KIND_OF based on CatalogSpec inspection."""
    from dental_bridge.adapters.gesden.extractors.catalogs import CATALOG_SPECS
    from dental_bridge.core.canonical.catalog_item import CatalogKind

    # Hard-coded — the source schema only has two hierarchies in v0.1.
    parents: dict[CatalogKind, CatalogKind] = {
        CatalogKind.PROVINCE: CatalogKind.COUNTRY,
        CatalogKind.CITY: CatalogKind.PROVINCE,
    }
    for spec in CATALOG_SPECS:
        parent = parents.get(spec.kind)
        if parent is not None:
            _PARENT_KIND_OF[spec.kind] = parent.value


_register_parent_links()
