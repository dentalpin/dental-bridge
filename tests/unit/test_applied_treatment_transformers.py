"""Tests for the applied-treatment and applied-treatment-phase transformers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.applied_treatment_phases import (
    transform as transform_phase,
)
from dental_bridge.adapters.gesden.transformers.applied_treatments import (
    transform as transform_applied,
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


def _baseline_applied() -> dict[str, object]:
    return {
        "Ident": 12345,
        "IdPac": 42,
        "NumTto": "T-2026-001",
        "IdTto": 200,
        "IdCol": 7,
        "IdColAux": None,
        "IdCli": 50,
        "IdUser": 10,
        "IdCentro": 1,
        "IdPresuTto": 9999,
        "IdRef": 0,
        "IdTipoEspec": 1,
        "NumDocUnico": "F2026/123",
        "NumTransaccion": "T-9000",
        "StaTto": 5,
        "FecIni": date(2026, 1, 15),
        "FecFin": None,
        "FechaCaduc": None,
        "FechaValida": None,
        "Importe": 120.0,
        "Dto": 0.0,
        "ImporteDto": 0.0,
        "Pendiente": 0.0,
        "ImportePrivado": 120.0,
        "ImporteMutua": 0.0,
        "Actos": 1,
        "Tiempo": 30,
        "SesRealiz": 1,
        "Notas": "OK",
        "ZonasBoca": 0,
        "PiezasAdu": 0,
        "PiezasLec": 0,
        "PiezasNum": 0,
        "ZonasPieza": 1073741824,  # 2^30, raw bit-mask
        "IdTipoOdg": 22,
        "Cuadrantes": 0,
        "Arcadas": 0,
        "DespX": 0,
        "DespY": 0,
        "Rotacion": 0,
        "Guid_Tenant": "abc",
    }


def test_baseline_applied_treatment() -> None:
    t = transform_applied(_baseline_applied(), _ctx())
    assert t.source_id == "12345"
    assert t.patient_uuid == derive_canonical_uuid("gesden", "patient", "42")
    assert t.client_uuid == derive_canonical_uuid("gesden", "client", "50")
    assert t.professional_uuid == derive_canonical_uuid("gesden", "professional", "7")
    assert t.treatment_variant_uuid == derive_canonical_uuid(
        "gesden", "treatment_catalog_variant", "200"
    )
    assert t.budget_line_uuid == derive_canonical_uuid("gesden", "budget_line", "9999")
    assert t.status_code == 5
    assert t.amount == Decimal("120.0")
    assert t.notes == "OK"
    assert t.document_number == "F2026/123"
    assert t.transaction_number == "T-9000"


def test_odontogram_raw_preserved() -> None:
    t = transform_applied(_baseline_applied(), _ctx())
    od = t.odontogram_raw
    # Snake-cased copies of every source bit-mask column.
    assert od["zonas_pieza"] == 1073741824
    assert od["id_tipo_odg"] == 22
    assert "piezas_adu" in od
    assert "piezas_lec" in od
    assert "cuadrantes" in od
    assert "rotacion" in od


def test_applied_treatment_phase() -> None:
    row = {
        "IdTtosMedFase": 5000,
        "IdTtosMed": 12345,
        "IdTratamientoFase": 99,
        "IdCol": 7,
        "IdColAux": None,
        "NumFase": 1,
        "Estado": 5,
        "Fecha": date(2026, 1, 20),
        "TpcFacturar": 100.0,
        "Notas": None,
        "Guid_Tenant": "abc",
    }
    p = transform_phase(row, _ctx())
    assert p.applied_treatment_uuid == derive_canonical_uuid("gesden", "applied_treatment", "12345")
    assert p.phase_template_uuid == derive_canonical_uuid(
        "gesden", "treatment_phase_template", "99"
    )
    assert p.phase_number == 1
    assert p.status_code == 5
    assert p.executed_on == date(2026, 1, 20)
    assert p.percent_to_bill == Decimal("100.0")
