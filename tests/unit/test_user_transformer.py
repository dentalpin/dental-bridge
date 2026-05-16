"""Tests for the user transformer."""

from __future__ import annotations

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.users import transform
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


def test_user_links_to_professional_when_id_col_present() -> None:
    row = {
        "IdUser": 10,
        "Login": "marta.garcia",
        "Nombre": "Marta",
        "Apellidos": "García",
        "IdCol": 7,
    }
    u = transform(row, _ctx())
    assert u.login == "marta.garcia"
    assert u.professional_uuid == derive_canonical_uuid("gesden", "professional", "7")


def test_user_without_professional_link() -> None:
    row = {
        "IdUser": 11,
        "Login": "admin",
        "Nombre": "Admin",
        "Apellidos": None,
        "IdCol": 0,
    }
    u = transform(row, _ctx())
    assert u.professional_uuid is None


def test_user_payload_carries_no_password() -> None:
    row = {
        "IdUser": 12,
        "Login": "alice",
        "Nombre": "Alice",
        "Apellidos": "Doe",
        "IdCol": None,
    }
    u = transform(row, _ctx())
    payload = u.model_dump()
    assert "Pass" not in payload
    assert "Password" not in payload
