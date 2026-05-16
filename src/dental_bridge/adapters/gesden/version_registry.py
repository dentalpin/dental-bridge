"""Catalogue of known Gesdén schema fingerprints.

When the connection module computes a fingerprint at startup, the result
is looked up here. An unknown fingerprint is a hard stop in production
mode — the operator is asked to file an issue and attach the fingerprint
plus the Gesdén version, so we can publish a new entry rather than guess.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnownFingerprint:
    fingerprint: str
    description: str
    adapter_versions: tuple[str, ...]


# Bootstrap entry: the development database under ``data/SOURCE_DB.MDF``.
# The actual hash will be populated by Sprint 1's first run against that
# database; until then, an empty registry means every connection is
# treated as unknown and the operator must pass ``--allow-unknown-schema``
# to proceed.
KNOWN_FINGERPRINTS: tuple[KnownFingerprint, ...] = ()


def lookup(fingerprint: str) -> KnownFingerprint | None:
    for entry in KNOWN_FINGERPRINTS:
        if entry.fingerprint == fingerprint:
            return entry
    return None
