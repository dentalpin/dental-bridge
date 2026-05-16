"""Decode Gesdén's integer-encoded time-of-day columns.

Gesdén stores ``DCitas.Hora`` (and the ``Duracion`` column) as an
integer expressing **seconds since midnight**. So 32400 means 09:00,
54000 means 15:00, 47700 means 13:15. Values outside [0, 86400) decode
to ``None``.

The hypothesis was confirmed against the development SOURCE_DB
database: the values are not minutes since midnight as legacy Gesdén
documentation sometimes suggests.
"""

from __future__ import annotations

from datetime import time

_MAX_SECONDS = 24 * 60 * 60  # 86400


def decode_gesden_time(value: object | None) -> time | None:
    """Return a ``time`` for valid second counts, otherwise ``None``."""
    if value is None or value == "":
        return None
    if isinstance(value, time):
        return value
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return None
    if as_int < 0 or as_int >= _MAX_SECONDS:
        return None
    hour, remainder = divmod(as_int, 3600)
    minute, second = divmod(remainder, 60)
    return time(hour=hour, minute=minute, second=second)


def decode_gesden_duration_seconds_to_minutes(value: object | None) -> int | None:
    """Convert a Gesdén duration-in-seconds integer into whole minutes.

    The canonical model carries durations in minutes; the source carries
    them in seconds. Sub-minute residue (rare) is dropped.
    """
    if value is None or value == "":
        return None
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return None
    if as_int < 0:
        return None
    return as_int // 60
