"""Tests for the Gesdén sentinel-date decoder."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        (date(1900, 1, 1), None),
        (date(1900, 1, 2), None),
        (date(1900, 1, 25), None),
        (date(1949, 12, 31), None),
        (date(1950, 1, 1), date(1950, 1, 1)),
        (date(2026, 5, 13), date(2026, 5, 13)),
        (datetime(2020, 6, 15, 9, 0), date(2020, 6, 15)),
        (datetime(1900, 1, 1, 0, 0), None),
    ],
)
def test_clean_date(raw: object, expected: date | None) -> None:
    assert clean_date(raw) == expected


def test_clean_date_tolerates_non_date_inputs() -> None:
    """Gesdén soft-delete columns flip types across builds; the decoder
    accepts whatever shows up and decodes anything non-date to None."""
    assert clean_date(42) is None
    assert clean_date(1) is None
    assert clean_date(True) is None
    assert clean_date("not-a-date") is None
    assert clean_date(b"\x01") is None
