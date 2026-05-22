"""Tests for the professional transformer."""

from __future__ import annotations

from datetime import date, datetime

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


def test_activo_s_yields_active() -> None:
    row = {
        "pk": "5",
        "Codigo": None,
        "Nombre": "Ana",
        "Apellidos": "Ruiz",
        "NIF": None,
        "IdTipoColab": 1,
        "Activo": "S",
        "FecBaja": None,
        "LastActivityAt": datetime(2026, 4, 10),
    }
    p = transform(row, _ctx())
    assert p.deactivated is False
    assert p.last_activity_at == date(2026, 4, 10)


def test_activo_n_yields_deactivated() -> None:
    row = {
        "pk": "5",
        "Apellidos": "Ruiz",
        "IdTipoColab": 1,
        "Activo": "N",
        "FecBaja": None,
        "LastActivityAt": None,
    }
    p = transform(row, _ctx())
    assert p.deactivated is True
    assert p.last_activity_at is None


def test_fecbaja_overrides_activo() -> None:
    # In some installs ``Activo`` stays 'S' but ``FecBaja`` is set when the
    # collaborator leaves. Either signal must mark the row as deactivated.
    row = {
        "pk": "5",
        "Apellidos": "Ruiz",
        "IdTipoColab": 1,
        "Activo": "S",
        "FecBaja": datetime(2023, 6, 1),
        "LastActivityAt": None,
    }
    p = transform(row, _ctx())
    assert p.deactivated is True


def test_sentinel_fecbaja_does_not_deactivate() -> None:
    # ``FecBaja`` defaulted to a 1900 sentinel is treated as "no leave date".
    row = {
        "pk": "5",
        "Apellidos": "Ruiz",
        "IdTipoColab": 1,
        "Activo": "S",
        "FecBaja": datetime(1900, 1, 1),
        "LastActivityAt": None,
    }
    p = transform(row, _ctx())
    assert p.deactivated is False


def test_tusuagd_orphan_keeps_synthetic_pk_and_role_other() -> None:
    row = {
        "pk": "usuagd:14",
        "Codigo": None,
        "Nombre": None,
        "Apellidos": "DRA. FACIL",
        "NIF": None,
        "IdTipoColab": None,
        # extractor projects TUsuAgd.Status into the same 'S'/'N' alphabet
        "Activo": "N",
        "FecBaja": None,
        "LastActivityAt": None,
    }
    p = transform(row, _ctx())
    assert p.source_id == "usuagd:14"
    assert p.role is ProfessionalRole.OTHER
    assert p.deactivated is True


def test_last_activity_accepts_string_iso_dates() -> None:
    # pyodbc returns datetimes natively, but downstream JSON round-trips
    # store the value as an ISO string in raw_source_data — confirm we
    # do not crash on the string path (clean_date returns None for str).
    row = {
        "pk": "5",
        "Apellidos": "Ruiz",
        "IdTipoColab": 1,
        "Activo": "S",
        "FecBaja": None,
        "LastActivityAt": "2025-12-15",
    }
    p = transform(row, _ctx())
    # clean_date is conservative with strings; the bridge never receives
    # one from pyodbc but we want a non-throwing fallback.
    assert p.last_activity_at is None
