"""Decode Gesdén's integer-encoded date columns.

Gesdén stores ``DCitas.Fecha`` (and a handful of other columns) as a
32-bit integer expressing **days since the OLE Automation epoch**
(1899-12-30). For example, 46241 represents 2026-08-12.

This was empirically determined against a real SOURCE_DB database:
``Hora`` columns turn out to be seconds-since-midnight and ``Fecha``
columns share Delphi/Excel-style date semantics, which is the OLE
epoch.

The decoder is defensive:

- Returns ``None`` for null / zero / sentinel values.
- Returns ``None`` for values that decode to an implausible date
  (before 1950 or after 2100), so a downstream warning can flag the
  row for manual review rather than silently producing a real date
  from corrupt data.
"""

from __future__ import annotations

from datetime import date, timedelta

# OLE Automation Date epoch (Windows COM / Excel / Delphi).
_EPOCH = date(1899, 12, 30)
_MIN_YEAR = 1950
_MAX_YEAR = 2100


def decode_gesden_date(value: object | None) -> date | None:
    """Return a ``date`` for non-sentinel integers, otherwise ``None``."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return None
    if as_int <= 0:
        return None
    try:
        result = _EPOCH + timedelta(days=as_int)
    except OverflowError:
        return None
    if result.year < _MIN_YEAR or result.year > _MAX_YEAR:
        return None
    return result
