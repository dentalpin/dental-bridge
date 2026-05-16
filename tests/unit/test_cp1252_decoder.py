"""Tests for the CP1252 fallback decoder."""

from __future__ import annotations

import pytest

from dental_bridge.adapters.gesden.decoders.encoding_cp1252 import decode_cp1252_bytes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("García", "García"),
        ("García".encode("cp1252"), "García"),
        ("Núñez Año".encode("cp1252"), "Núñez Año"),
        (b"", ""),
    ],
)
def test_decode_cp1252_bytes(raw: object, expected: str | None) -> None:
    assert decode_cp1252_bytes(raw) == expected
