"""Tests for the budget and budget-line transformers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.budget_lines import (
    transform as transform_line,
)
from dental_bridge.adapters.gesden.transformers.budgets import (
    transform as transform_budget,
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


def test_baseline_budget() -> None:
    row = {
        "Ident": 555,
        "IdPac": 42,
        "NumSerie": 1,
        "NumPre": 100,
        "Titulo": "Presupuesto inicial",
        "Notas": None,
        "FecPresup": date(2026, 1, 10),
        "FecAcepta": None,
        "FecRechaz": None,
        "ObsRechaz": None,
        "IdCol": 7,
        "IdCentro": 1,
        "IdUserElabora": 10,
        "IdUserPresentacion": 10,
        "Estado": 2,
        "EsAlternativa": 0,
        "AlternativaDe": None,
        "Id_PresuOriginal": None,
        "Id_UserRechaz": None,
        "Hash": "deadbeef",
        "HashControl": "abc123",
        "CodigoATCUD": None,
        "CodigoQR": None,
        "Guid_Tenant": "abc",
    }
    b = transform_budget(row, _ctx())
    assert b.source_id == "555"
    assert b.patient_uuid == derive_canonical_uuid("gesden", "patient", "42")
    assert b.number == 100
    assert b.title == "Presupuesto inicial"
    assert b.legal_hash == "deadbeef"
    assert b.is_alternative is False
    assert b.status_code == 2


def test_budget_double_link_to_applied_treatment() -> None:
    row = {
        "Ident": 1001,
        "Id_Presu": 555,
        "IdPac": 42,
        "NumSerie": 1,
        "NumPre": 100,
        "LinPre": 1,
        "IdTto": 200,
        "IdTratamiento": 7,
        "IdTtoMedOrig": 12345,  # ← forward half of the double link
        "IdCol": 7,
        "IdColAux": None,
        "IdCli": 50,
        "Orden": 1,
        "StaTto": 3,
        "Unidades": 1.0,
        "ImportePre": 120.0,
        "ImporteUni": 120.0,
        "Dto": 0.0,
        "ImporteDto": 0.0,
        "BaseImponible": 99.17,
        "IdTipoIVA": 1,
        "TpcIVA": 21.0,
        "ImporteIVA": 20.83,
        "FecIni": None,
        "FecFin": None,
        "FecAcepta": None,
        "Notas": None,
        "Tiempo": 30,
        "ZonasBoca": 0,
        "PiezasAdu": 0,
        "PiezasLec": 0,
        "PiezasNum": 0,
        "ZonasPieza": 16777216,
        "IdTipoOdg": 22,
        "Cuadrantes": 0,
        "Arcadas": 0,
        "DespX": 0,
        "DespY": 0,
        "Rotacion": 0,
        "Guid_Tenant": "abc",
    }
    line = transform_line(row, _ctx())
    assert line.budget_uuid == derive_canonical_uuid("gesden", "budget", "555")
    assert line.applied_treatment_uuid == derive_canonical_uuid(
        "gesden", "applied_treatment", "12345"
    )
    assert line.unit_amount == Decimal("120.0")
    assert line.base_amount == Decimal("99.17")
    assert line.vat_percent == Decimal("21.0")
    assert line.odontogram_raw["zonas_pieza"] == 16777216
