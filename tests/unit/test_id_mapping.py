"""Tests for the in-memory ID-mapping registry."""

from __future__ import annotations

from uuid import UUID

import pytest

from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.id_mapping import IdMapping


def test_register_returns_deterministic_uuid() -> None:
    mapping = IdMapping()
    uuid_a = mapping.register("gesden", "patient", 42)
    uuid_b = mapping.register("gesden", "patient", 42)
    assert uuid_a == uuid_b
    assert uuid_a == derive_canonical_uuid("gesden", "patient", "42")


def test_register_distinguishes_entity_type() -> None:
    mapping = IdMapping()
    patient_uuid = mapping.register("gesden", "patient", 1)
    client_uuid = mapping.register("gesden", "client", 1)
    assert patient_uuid != client_uuid


def test_resolve_returns_deterministic_when_not_required() -> None:
    mapping = IdMapping()
    resolved = mapping.resolve("gesden", "patient", 99)
    assert isinstance(resolved, UUID)
    assert resolved == derive_canonical_uuid("gesden", "patient", "99")


def test_resolve_require_known_returns_none_for_unseen() -> None:
    mapping = IdMapping()
    assert mapping.resolve("gesden", "patient", 99, require_known=True) is None
    mapping.register("gesden", "patient", 99)
    assert mapping.resolve("gesden", "patient", 99, require_known=True) is not None


def test_resolve_skips_null_and_empty() -> None:
    mapping = IdMapping()
    assert mapping.resolve("gesden", "patient", None) is None
    assert mapping.resolve("gesden", "patient", "") is None


def test_register_rejects_implausibly_long_id() -> None:
    mapping = IdMapping()
    with pytest.raises(ValueError):
        mapping.register("gesden", "patient", "x" * 1024)
