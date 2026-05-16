"""Tests for the Gesdén patient transformer."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.patients import transform
from dental_bridge.core.canonical._enums import Sex
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


def _baseline_row() -> dict[str, object]:
    return {
        "IdPac": 100,
        "NumPac": "0042",
        "Nombre": "  Carlos  ",
        "Apellidos": "García Núñez",
        "NIF": "  12345678a ",
        "FecNacim": date(1980, 5, 1),
        "FecAlta": date(2015, 9, 12),
        "Sexo": "H",
        "Inactivo": None,
        "Exitus": 0,
        "AceptaLOPD": 1,
        "IdCli": 200,
        "IdCliTutor": None,
        "IdCliPac": None,
        "IdCliDefec": 200,
        "IdCol": 3,
        "IdCentro": 1,
        "IdPacReferidor": None,
        "Guid_Tenant": "f7d6c3a0-1111-2222-3333-deadbeefcafe",
    }


def test_baseline_patient_maps_cleanly() -> None:
    ctx = _ctx()
    p = transform(_baseline_row(), ctx)
    assert p.source_id == "100"
    assert p.canonical_uuid == derive_canonical_uuid("gesden", "patient", "100")
    assert p.given_name == "Carlos"
    assert p.family_name == "García Núñez"
    assert p.national_id == "12345678A"
    assert p.date_of_birth == date(1980, 5, 1)
    assert p.sex is Sex.MALE
    assert p.deceased is False
    assert p.deactivated_at is None
    assert p.gdpr_consent is True
    assert p.tenant_label == "f7d6c3a0-1111-2222-3333-deadbeefcafe"


def test_sentinel_dob_becomes_null() -> None:
    row = _baseline_row()
    row["FecNacim"] = date(1900, 1, 1)
    p = transform(row, _ctx())
    assert p.date_of_birth is None


def test_inactive_smalldatetime_sets_deactivated_at() -> None:
    row = _baseline_row()
    row["Inactivo"] = datetime(2021, 3, 4, 10, 0)
    p = transform(row, _ctx())
    assert p.deactivated_at == date(2021, 3, 4)


def test_inactive_as_bit_flag_does_not_set_deactivated_at() -> None:
    row = _baseline_row()
    row["Inactivo"] = 1  # newer Gesdén builds store Inactivo as a bit
    p = transform(row, _ctx())
    assert p.deactivated_at is None


def test_exitus_flag_marks_deceased() -> None:
    row = _baseline_row()
    row["Exitus"] = 1
    p = transform(row, _ctx())
    assert p.deceased is True


def test_guardian_link_resolved_via_id_mapping() -> None:
    row = _baseline_row()
    row["IdCliTutor"] = 501
    p = transform(row, _ctx())
    assert p.guardian_client_uuid == derive_canonical_uuid("gesden", "client", "501")


def test_referrer_self_fk_resolved() -> None:
    row = _baseline_row()
    row["IdPacReferidor"] = 99
    p = transform(row, _ctx())
    assert p.referrer_patient_uuid == derive_canonical_uuid("gesden", "patient", "99")


def test_self_referrer_to_own_id_is_ignored() -> None:
    row = _baseline_row()
    row["IdPacReferidor"] = row["IdPac"]
    p = transform(row, _ctx())
    assert p.referrer_patient_uuid is None


def test_center_sentinel_minus_one_treated_as_null() -> None:
    row = _baseline_row()
    row["IdCentro"] = -1
    p = transform(row, _ctx())
    assert p.default_center_uuid is None


def test_unknown_sex_token_emits_warning() -> None:
    ctx = _ctx()
    row = _baseline_row()
    row["Sexo"] = "Z"
    p = transform(row, ctx)
    assert p.sex is Sex.UNKNOWN
    codes = [w.code for w in ctx.warnings]
    assert "patient.sex.unknown_token" in codes


def test_tenant_mismatch_emits_error_warning() -> None:
    ctx = _ctx()
    transform(_baseline_row(), ctx)
    second = _baseline_row()
    second["IdPac"] = 101
    second["Guid_Tenant"] = "00000000-0000-0000-0000-000000000000"
    transform(second, ctx)
    codes = [w.code for w in ctx.warnings]
    assert "patient.tenant.mismatch" in codes


def test_empty_nif_becomes_none() -> None:
    row = _baseline_row()
    row["NIF"] = "   "
    p = transform(row, _ctx())
    assert p.national_id is None


def test_raw_source_data_preserves_original_strings() -> None:
    row = _baseline_row()
    p = transform(row, _ctx())
    assert p.raw_source_data["Nombre"] == "  Carlos  "  # unstripped on purpose
    assert p.raw_source_data["FecNacim"] == "1980-05-01"


@pytest.mark.parametrize(
    ("token", "expected"),
    [("H", Sex.MALE), ("V", Sex.MALE), ("M", Sex.FEMALE), ("F", Sex.FEMALE), ("", Sex.UNKNOWN)],
)
def test_sex_decoder_mapping(token: str, expected: Sex) -> None:
    row = _baseline_row()
    row["Sexo"] = token
    p = transform(row, _ctx())
    assert p.sex is expected
