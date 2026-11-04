"""The extract CLI selects origin adapters by their installed name."""

from __future__ import annotations

from pathlib import Path

from dental_bridge.adapters.gesden.adapter import GesdenAdapter
from dental_bridge.adapters.nemodent.adapter import NemodentAdapter
from dental_bridge.cli.extract import _guess_tenant_label, _resolve_adapter_class
from dental_bridge.core.adapters.registry import discover


def test_extract_defaults_to_gesden_when_no_adapter_option_is_given() -> None:
    available = {"gesden": GesdenAdapter, "nemodent": NemodentAdapter}

    assert _resolve_adapter_class("gesden", available) is GesdenAdapter


def test_extract_resolves_nemodent_from_the_registry() -> None:
    available = {"gesden": GesdenAdapter, "nemodent": NemodentAdapter}

    assert _resolve_adapter_class("nemodent", available) is NemodentAdapter


def test_built_in_adapters_are_registered_as_entry_points() -> None:
    available = discover()

    assert available["gesden"] is GesdenAdapter
    assert available["nemodent"] is NemodentAdapter


def test_extract_returns_none_for_an_unregistered_adapter() -> None:
    assert _resolve_adapter_class("missing", {}) is None


def test_nemodent_tenant_label_uses_mdb_filename() -> None:
    assert _guess_tenant_label(str(Path("clinic-copy.mdb")), adapter_name="nemodent") == (
        "clinic-copy"
    )
