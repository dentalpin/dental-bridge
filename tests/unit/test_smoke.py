"""Smoke tests — verify the package imports and the CLI is reachable."""

from __future__ import annotations


def test_package_imports() -> None:
    import dental_bridge

    assert dental_bridge.__version__


def test_cli_app_resolves() -> None:
    from dental_bridge.cli.app import app

    assert app.info.name == "dental-bridge"


def test_gesden_adapter_module_loads() -> None:
    from dental_bridge.adapters import gesden

    assert gesden.ADAPTER_NAME == "gesden"


def test_base_canonical_entity_rejects_extra_fields() -> None:
    import pytest
    from pydantic import ValidationError

    from dental_bridge.core.canonical.base import BaseCanonicalEntity

    with pytest.raises(ValidationError):
        BaseCanonicalEntity(
            canonical_uuid="00000000-0000-0000-0000-000000000000",
            source_system="x",
            entity_type="test",
            source_id="1",
            adapter_version="0.0.0",
            extracted_at="2026-01-01T00:00:00Z",
            raw_source_data={},
            unexpected_field=True,  # type: ignore[call-arg]
        )
