"""Identity transformer tests also protect the source-column allowlist."""

from __future__ import annotations

from datetime import date, datetime

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.centers import transform as transform_center
from dental_bridge.adapters.nemodent.transformers.patients import transform as transform_patient
from dental_bridge.adapters.nemodent.transformers.professionals import (
    transform as transform_professional,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.professional import ProfessionalRole
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context() -> TransformContext:
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
        tenant_label="test-clinic",
    )


def test_center_transform_uses_stable_identity_and_allowlisted_raw_data() -> None:
    context = _context()
    row = {
        "GUID": "center-1",
        "Name": "Clinic",
        "NIF": "X123",
        "Password": "must-not-export",
    }

    center = transform_center(row, context)

    assert center is not None
    assert center.canonical_uuid == derive_canonical_uuid("nemodent", "center", "center-1")
    assert center.name == "Clinic"
    assert "Password" not in center.raw_source_data


def test_professional_transform_never_exports_access_credentials() -> None:
    row = {
        "ID": "007",
        "First": "Ada",
        "Surname": "Example",
        "Type": "unknown-source-role",
        "Password": "secret",
        "ServicesPassword": "secret",
        "CalendarPassword": "secret",
        "UserName": "login",
    }
    context = _context()

    professional = transform_professional(row, context)

    assert professional is not None
    assert professional.source_id == "007"
    assert professional.role is ProfessionalRole.OTHER
    assert (
        not {
            "Password",
            "ServicesPassword",
            "CalendarPassword",
            "UserName",
        }
        & professional.raw_source_data.keys()
    )
    assert [warning.code for warning in context.warnings] == ["professional.role_unmapped"]


def test_patient_transform_preserves_unknown_sex_without_guessing() -> None:
    context = _context()
    row = {
        "GUID": "patient-1",
        "First": "Example",
        "SurName": "Patient",
        "SexCode": 1,
        "BirthDate": datetime(2000, 1, 2),
        "AdmissionDate": date(2020, 5, 6),
        "GUID_ACCOUNT": "ledger-account-1",
        "GUID_ACCOUNT_HOLDER": "holder-account-1",
        "GUID_REFERRER_PATIENT": "external-referrer-1",
        "Holder": False,
        "ServicesPassword": "must-not-export",
    }

    patient = transform_patient(row, context)

    assert patient is not None
    assert patient.sex.value == "unknown"
    assert patient.date_of_birth == date(2000, 1, 2)
    assert patient.raw_source_data["AdmissionDate"] == "2020-05-06"
    assert patient.raw_source_data["GUID_ACCOUNT"] == "ledger-account-1"
    assert patient.raw_source_data["GUID_ACCOUNT_HOLDER"] == "holder-account-1"
    assert patient.raw_source_data["GUID_REFERRER_PATIENT"] == "external-referrer-1"
    assert patient.raw_source_data["Holder"] is False
    assert patient.referrer_patient_uuid is None
    assert "ServicesPassword" not in patient.raw_source_data
    assert [warning.code for warning in context.warnings] == [
        "patient.sex_unmapped",
        "patient.payer_link_unmapped",
        "patient.external_referrer_unmapped",
    ]
