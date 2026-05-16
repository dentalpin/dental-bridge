"""Tests for the Gesdén YYYYMMDD-int date decoder."""

from __future__ import annotations

from datetime import date

import pytest

from dental_bridge.adapters.gesden.decoders.gesden_date import decode_gesden_date


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        (0, None),
        (-5, None),
        # Days since OLE epoch 1899-12-30. Empirically validated against a
        # real Gesdén SOURCE_DB database.
        (46241, date(2026, 8, 7)),
        ("46241", date(2026, 8, 7)),
        (18264, date(1950, 1, 1)),  # epoch + 18264 days
        (1000, None),  # year 1902 — below floor
        (73050, date(2099, 12, 31)),
        ("not-a-number", None),
        (date(2024, 6, 1), date(2024, 6, 1)),
    ],
)
def test_decode_gesden_date(raw: object, expected: date | None) -> None:
    assert decode_gesden_date(raw) == expected
