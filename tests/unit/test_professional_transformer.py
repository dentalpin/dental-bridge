"""Tests for the professional transformer."""

from __future__ import annotations

import pytest

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.professionals import transform
from dental_bridge.core.canonical.professional import ProfessionalRole
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def test_basic_mapping() -> None:
    row = {
        "IdCol": 7,
        "Codigo": "DR-MGarcia",
        "Nombre": "Marta",
        "Apellidos": "García",
        "NIF": "  98765432z ",
        "IdTipoColab": 1,
    }
    p = transform(row, _ctx())
    assert p.given_name == "Marta"
    assert p.family_name == "García"
    assert p.national_id == "98765432Z"
    assert p.role is ProfessionalRole.DOCTOR


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (1, ProfessionalRole.DOCTOR),
        (2, ProfessionalRole.HYGIENIST),
        (3, ProfessionalRole.AUXILIARY),
        (4, ProfessionalRole.ADMIN),
        (99, ProfessionalRole.OTHER),
        (None, ProfessionalRole.OTHER),
    ],
)
def test_role_decoder(code: object, expected: ProfessionalRole) -> None:
    row = {
        "IdCol": 1,
        "Codigo": "x",
        "Nombre": "x",
        "Apellidos": "x",
        "NIF": "",
        "IdTipoColab": code,
    }
    p = transform(row, _ctx())
    assert p.role is expected
