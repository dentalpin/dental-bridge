"""Tests for the Gesdén minutes-since-midnight time decoder."""

from __future__ import annotations

from datetime import time

import pytest

from dental_bridge.adapters.gesden.decoders.gesden_time import (
    decode_gesden_duration_seconds_to_minutes,
    decode_gesden_time,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        (0, time(0, 0)),
        (32400, time(9, 0)),  # 9 * 3600
        (47700, time(13, 15)),  # 13:15
        (54000, time(15, 0)),
        (86399, time(23, 59, 59)),
        (86400, None),  # out of range
        (-1, None),
        ("nope", None),
        (time(10, 30), time(10, 30)),
    ],
)
def test_decode_gesden_time(raw: object, expected: time | None) -> None:
    assert decode_gesden_time(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        ("", None),
        (-1, None),
        (0, 0),
        (1800, 30),
        (2700, 45),
        (3600, 60),
        (21600, 360),
        ("900", 15),
    ],
)
def test_decode_duration_seconds_to_minutes(raw: object, expected: int | None) -> None:
    assert decode_gesden_duration_seconds_to_minutes(raw) == expected
