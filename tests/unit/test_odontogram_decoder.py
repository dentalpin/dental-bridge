"""Tests for the Gesdén odontogram decoder.

The mapping was reverse-engineered from frequency analysis of
``SOURCE_DB``'s ``IdTipoOdg=24`` (implants) — the top bit positions
should correspond to first molars (FDI 16, 26, 36, 46), the most
common implant sites.
"""

from __future__ import annotations

import pytest

from dental_bridge.adapters.gesden.decoders.odontogram import (
    decode_piezas_adu,
    decode_piezas_lec,
)


def test_zero_returns_empty() -> None:
    assert decode_piezas_adu(0) == []
    assert decode_piezas_adu(None) == []
    assert decode_piezas_adu("") == []
    assert decode_piezas_lec(0) == []
    assert decode_piezas_lec(None) == []


def test_invalid_value_returns_empty() -> None:
    assert decode_piezas_adu("nope") == []
    assert decode_piezas_adu(-5) == []


@pytest.mark.parametrize(
    ("bit", "expected_fdi"),
    [
        # Reverse-engineered alignment: the four most-frequent implant
        # bits map to the four first molars (one per quadrant).
        (2, 16),  # UR1st molar (755 implants observed)
        (13, 26),  # UL1st molar (753)
        (18, 46),  # LR1st molar (603)
        (29, 36),  # LL1st molar (526)
        # Quadrant extremes per the documented order.
        (0, 18),  # UR third molar
        (7, 11),  # UR central incisor
        (8, 21),  # UL central incisor
        (15, 28),  # UL third molar
        (16, 48),  # LR third molar
        (23, 41),  # LR central incisor
        (24, 31),  # LL central incisor
        (31, 38),  # LL third molar
    ],
)
def test_single_bit_decodes_to_expected_fdi(bit: int, expected_fdi: int) -> None:
    assert decode_piezas_adu(1 << bit) == [expected_fdi]


def test_multiple_bits_decode_in_low_to_high_order() -> None:
    # Bits 2 + 13 → upper right + upper left first molars (bridge candidates).
    value = (1 << 2) | (1 << 13)
    assert decode_piezas_adu(value) == [16, 26]


def test_bits_outside_adult_range_are_skipped() -> None:
    # Bit 32 (and beyond) has no adult FDI mapping; bit 5 (FDI 13) does.
    value = (1 << 5) | (1 << 40)
    assert decode_piezas_adu(value) == [13]


def test_piezas_lec_quadrant_extremes() -> None:
    # First deciduous quadrant (UR) is bits 0-4 → FDI 55..51.
    assert decode_piezas_lec(1 << 0) == [55]
    assert decode_piezas_lec(1 << 4) == [51]
    # Out-of-range bit is skipped.
    assert decode_piezas_lec(1 << 25) == []
