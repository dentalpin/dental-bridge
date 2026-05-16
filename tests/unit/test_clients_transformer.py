"""Tests for the Gesdén client transformer."""

from __future__ import annotations

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.clients import transform
from dental_bridge.core.canonical._enums import ClientKind
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


def test_person_client_is_classified_as_person() -> None:
    row = {
        "IdCli": 1,
        "Nombre": "Ana",
        "Apellidos": "López",
        "RazonSocial": None,
        "NIF": "12345678b",
        "Email": "ana@example.com",
        "IdCentro": 1,
        "IdCIA": None,
        "Guid_Tenant": "abc",
    }
    c = transform(row, _ctx())
    assert c.kind is ClientKind.PERSON
    assert c.given_name == "Ana"
    assert c.family_name == "López"
    assert c.legal_name is None
    assert c.national_id == "12345678B"


def test_company_client_is_classified_as_company() -> None:
    row = {
        "IdCli": 2,
        "Nombre": None,
        "Apellidos": None,
        "RazonSocial": "Mutua Dental S.A.",
        "NIF": "A12345678",
        "Email": "info@mutua.example",
        "IdCentro": 1,
        "IdCIA": None,
        "Guid_Tenant": "abc",
    }
    c = transform(row, _ctx())
    assert c.kind is ClientKind.COMPANY
    assert c.legal_name == "Mutua Dental S.A."
    assert c.given_name is None
    assert c.family_name is None


def test_parent_company_uuid_resolved() -> None:
    row = {
        "IdCli": 3,
        "Nombre": None,
        "Apellidos": None,
        "RazonSocial": "Sucursal Madrid",
        "NIF": None,
        "Email": None,
        "IdCentro": 1,
        "IdCIA": 99,
        "Guid_Tenant": "abc",
    }
    c = transform(row, _ctx())
    assert c.parent_company_uuid == derive_canonical_uuid("gesden", "client", "99")


def test_self_referencing_parent_is_ignored() -> None:
    row = {
        "IdCli": 7,
        "Nombre": None,
        "Apellidos": None,
        "RazonSocial": "Self ref",
        "NIF": None,
        "Email": None,
        "IdCentro": None,
        "IdCIA": 7,
        "Guid_Tenant": "abc",
    }
    c = transform(row, _ctx())
    assert c.parent_company_uuid is None
