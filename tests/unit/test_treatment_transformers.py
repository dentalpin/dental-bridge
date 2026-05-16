"""Tests for the treatment catalog, variant, and phase-template transformers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.treatment_catalog_items import (
    transform as transform_template,
)
from dental_bridge.adapters.gesden.transformers.treatment_catalog_variants import (
    transform as transform_variant,
)
from dental_bridge.adapters.gesden.transformers.treatment_phase_templates import (
    transform as transform_phase,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def test_treatment_template_mapping() -> None:
    row = {
        "IdTratamiento": 7,
        "Codigo": "0123",
        "DescripMed": "Limpieza dental",
        "DescripPac": "Higiene oral",
        "DescripAgd": "Higiene",
        "IdTipoEspec": 1,
        "IdTipoODG": 38,
        "Duracion": 30,
        "NumFases": 1,
        "PrecioReferencia": 60.0,
        "Inactivo": 0,
        "Desde": date(2020, 1, 1),
        "Hasta": None,
        "Guid_Tenant": "abc",
    }
    t = transform_template(row, _ctx())
    assert t.code == "0123"
    assert t.description == "Limpieza dental"
    assert t.duration_minutes == 30
    assert t.reference_price == Decimal("60.0")
    assert t.deactivated is False
    assert t.specialty_uuid is not None
    assert t.odontogram_kind_uuid is not None


def test_variant_links_to_template() -> None:
    row = {
        "IdTratamientoTarifa": 200,
        "IdTratamiento": 7,
        "IdTarifa": 1,
        "CodTto": "T1-0123",
        "IdTipoEspec": 1,
        "IdGrupo": 0,
        "Inactivo": 0,
        "Guid_Tenant": "abc",
    }
    v = transform_variant(row, _ctx())
    assert v.treatment_uuid == derive_canonical_uuid("gesden", "treatment_catalog_item", "7")
    assert v.code == "T1-0123"
    assert v.tariff_code == "1"


def test_phase_template_links_to_template() -> None:
    row = {
        "IdTratamientoFase": 99,
        "IdTratamiento": 7,
        "DescripMed": "Fase 1: revisión",
        "Observaciones": None,
        "Duracion": 15,
        "TpcFacturar": 50.0,
        "OrdenEjecucion": 1,
        "MinDias": 0,
        "MaxDias": 7,
        "Guid_Tenant": "abc",
    }
    p = transform_phase(row, _ctx())
    assert p.treatment_uuid == derive_canonical_uuid("gesden", "treatment_catalog_item", "7")
    assert p.duration_minutes == 15
    assert p.percent_to_bill == Decimal("50.0")
    assert p.execution_order == 1
