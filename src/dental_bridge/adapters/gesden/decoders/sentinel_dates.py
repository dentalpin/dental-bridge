"""Map Gesdén sentinel dates to ``None``.

Gesdén persists "unknown" or "not applicable" dates as values around the
SQL Server epoch — 1900-01-01, 1900-01-02 and 1900-01-25 are the recurring
ones observed in `docs/schema_map.md` quirk #26. Anything older than 1950
is almost certainly sentinel rather than a real historical date for a
patient or transaction.
"""

from __future__ import annotations

from datetime import date, datetime

# Earliest date plausibly representing a real human event in this dataset.
# Patients born before 1925 are extremely rare; appointments and
# transactions before 1950 do not exist in any Gesdén-era PMS.
EARLIEST_PLAUSIBLE = date(1950, 1, 1)


def clean_date(value: object | None) -> date | None:
    """Return a ``date`` for non-sentinel values, otherwise ``None``.

    The function is permissive: anything that isn't a real, plausible
    date — booleans, integers, strings, sentinels — decodes to ``None``.
    Gesdén databases mix types in soft-delete columns across builds
    (``Inactivo`` is a bit, a smalldatetime or sometimes a string flag),
    so we tolerate them all and let the importer fall back to the raw
    payload when it needs the original value.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, int | float | str):
        return None
    if not isinstance(value, date):
        return None
    if value < EARLIEST_PLAUSIBLE:
        return None
    return value
