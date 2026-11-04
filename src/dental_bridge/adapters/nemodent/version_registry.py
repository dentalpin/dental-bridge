"""Known Nemodent schema fingerprints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnownFingerprint:
    fingerprint: str
    description: str
    adapter_versions: tuple[str, ...]


# Populate only from an authorized local schema-metadata scan. Never derive
# this registry from patient rows or commit a source database/schema dump.
KNOWN_FINGERPRINTS: tuple[KnownFingerprint, ...] = (
    KnownFingerprint(
        fingerprint="sha256:c2d199cb0c6a087a906a2e8b0e7fda25d768eb60cde990ec9da7b66b2bdff997",
        description="Nemodent reference database schema",
        adapter_versions=("0.1.0",),
    ),
)


def lookup(fingerprint: str) -> KnownFingerprint | None:
    return next((item for item in KNOWN_FINGERPRINTS if item.fingerprint == fingerprint), None)
