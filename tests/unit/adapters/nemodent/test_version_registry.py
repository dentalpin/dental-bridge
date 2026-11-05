"""Known schema fingerprint lookup tests."""

from __future__ import annotations

from dental_bridge.adapters.nemodent import version_registry


def test_unknown_fingerprint_returns_none() -> None:
    assert version_registry.lookup("sha256:not-registered") is None


def test_reference_schema_fingerprint_is_registered() -> None:
    known = version_registry.lookup(
        "sha256:c2d199cb0c6a087a906a2e8b0e7fda25d768eb60cde990ec9da7b66b2bdff997"
    )

    assert known is not None
    assert known.description == "Nemodent reference database schema"
    assert "0.1.0" in known.adapter_versions


def test_lookup_matches_registered_schema(monkeypatch) -> None:
    known = version_registry.KnownFingerprint(
        fingerprint="sha256:reference",
        description="Nemodent reference MDB",
        adapter_versions=("0.1.0",),
    )
    monkeypatch.setattr(version_registry, "KNOWN_FINGERPRINTS", (known,))

    assert version_registry.lookup("sha256:reference") is known
