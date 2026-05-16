"""Helpers for decoding Gesdén money/numeric columns."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def coerce_decimal(value: object | None) -> Decimal | None:
    """Best-effort decimal coercion; non-numeric values decode to ``None``.

    Gesdén stores monetary amounts as ``float`` (legacy) and ``numeric``
    (recent). Tests sometimes pass plain ints. We accept all of them and
    only refuse strings/Nones gracefully.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):  # bool is an int subclass — guard first
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def coerce_int(value: object | None) -> int | None:
    """Best-effort int coercion; non-numeric values decode to ``None``."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
