"""Tests for the centre transformer."""

from __future__ import annotations

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.centers import transform
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


def test_center_basic_mapping() -> None:
    row = {"IdCentro": 1, "CodCentro": "INFOMED", "Descripcio": "Clínica Central"}
    c = transform(row, _ctx())
    assert c.code == "INFOMED"
    assert c.name == "Clínica Central"
    assert c.canonical_uuid == derive_canonical_uuid("gesden", "center", "1")
