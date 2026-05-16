"""Shared enumerations used by multiple canonical entities."""

from __future__ import annotations

from enum import StrEnum


class Sex(StrEnum):
    """Biological sex as recorded by the source PMS.

    Kept deliberately small. Source systems that use richer gender taxonomies
    can record the original value in ``raw_source_data`` and map only the
    administrative-sex axis here.
    """

    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class ClientKind(StrEnum):
    """A `Client` may represent a natural person or a legal entity."""

    PERSON = "person"
    COMPANY = "company"
