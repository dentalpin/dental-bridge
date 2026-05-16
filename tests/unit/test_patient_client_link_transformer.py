"""Tests for the Gesdén PacCli (patient↔client) transformer."""

from __future__ import annotations

from datetime import date

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.patient_client_links import transform
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


def test_link_resolves_both_uuids_and_dates() -> None:
    row = {
        "IdPac": 100,
        "IdCli": 200,
        "Poliza": "POL-7",
        "FecAlta": date(2020, 1, 1),
        "FecCaduc": date(2021, 1, 1),
        "Inactivo": None,
    }
    link = transform(row, _ctx())
    assert link.patient_uuid == derive_canonical_uuid("gesden", "patient", "100")
    assert link.client_uuid == derive_canonical_uuid("gesden", "client", "200")
    assert link.policy_number == "POL-7"
    assert link.valid_from == date(2020, 1, 1)
    assert link.valid_until == date(2021, 1, 1)
    assert link.source_id == "100:200"


def test_link_sentinel_dates_normalised() -> None:
    row = {
        "IdPac": 1,
        "IdCli": 2,
        "Poliza": None,
        "FecAlta": date(1900, 1, 1),
        "FecCaduc": None,
        "Inactivo": None,
    }
    link = transform(row, _ctx())
    assert link.valid_from is None
