"""Shared state passed to every transformer call."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


@dataclass(slots=True)
class TransformContext:
    """Bag of references every transformer needs."""

    source_system: str
    adapter_version: str
    id_mapping: IdMapping
    warnings: WarningRegistry
    # The Guid_Tenant value observed on the first row. Subsequent rows with
    # a different value are flagged as warnings and the run is aborted by
    # the adapter at a higher level.
    tenant_label: str | None = None

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)


def normalise_string(value: object | None) -> str | None:
    """Strip whitespace and treat empty strings as null.

    Source columns are nvarchar/varchar with trailing-space padding in older
    Gesdén versions. We never want a literal empty string in a canonical
    entity — either there is a value or there isn't.
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalise_national_id(value: object | None) -> str | None:
    """Uppercase and strip; do not validate.

    Source data is dirty (mix of NIF, NIE, passport numbers, blanks,
    sometimes phone numbers in the wrong column). Validation belongs to the
    destination importer, which knows its own rules.
    """
    text = normalise_string(value)
    return text.upper() if text is not None else None


def serialise_raw(row: dict[str, object]) -> dict[str, object]:
    """Build a JSON-serialisable copy of a raw row.

    Coerces ``datetime``/``date`` to ISO strings and ``bytes`` to hex.
    Anything else is passed through and will surface as a ``TypeError``
    in the writer if not natively serialisable — that is preferable to
    silently dropping data we did not anticipate.
    """
    from datetime import date as _date
    from datetime import datetime as _dt

    out: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, _dt | _date):
            out[key] = value.isoformat()
        elif isinstance(value, bytes):
            out[key] = value.hex()
        else:
            out[key] = value
    return out


def tenant_str(value: object | None) -> str | None:
    """Coerce a Gesdén ``Guid_Tenant`` value to a string, treating empty as None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
