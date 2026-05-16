"""Tests for the generic catalog transformer."""

from __future__ import annotations

from dental_bridge.adapters.gesden.extractors.catalogs import SPECS_BY_KIND
from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.catalogs import transform
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.catalog_item import CatalogKind
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def test_country_row_maps_to_canonical_country() -> None:
    spec = SPECS_BY_KIND[CatalogKind.COUNTRY]
    row = {"IdPais": 1, "IsoAlfa2": "ES", "Descripcio": "España"}
    c = transform(row, _ctx(), spec=spec)
    assert c.kind is CatalogKind.COUNTRY
    assert c.code == "ES"
    assert c.name == "España"
    assert c.parent_uuid is None
    assert c.source_id == "country:1"


def test_province_row_resolves_parent_country() -> None:
    spec = SPECS_BY_KIND[CatalogKind.PROVINCE]
    row = {"IdProvin": 28, "IdPais": 1, "CodPro": "M", "Descripcio": "Madrid"}
    p = transform(row, _ctx(), spec=spec)
    expected_parent = derive_canonical_uuid("gesden", "catalog_item", "country:1")
    assert p.parent_uuid == expected_parent


def test_city_row_resolves_parent_province() -> None:
    spec = SPECS_BY_KIND[CatalogKind.CITY]
    row = {"IdPoblacio": 100, "IdProvin": 28, "CodINE": "MAD", "Descripcio": "Madrid capital"}
    c = transform(row, _ctx(), spec=spec)
    expected_parent = derive_canonical_uuid("gesden", "catalog_item", "province:28")
    assert c.parent_uuid == expected_parent


def test_flat_catalog_has_no_parent_link() -> None:
    spec = SPECS_BY_KIND[CatalogKind.PAYMENT_METHOD]
    row = {"IdForPago": 1, "Tipo": "EFECTIVO", "Descripcio": "Efectivo"}
    p = transform(row, _ctx(), spec=spec)
    assert p.parent_uuid is None
