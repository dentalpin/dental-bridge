"""CanonicalCatalogItem — a generic lookup-table entry.

Gesdén carries dozens of small reference tables (countries, provinces,
cities, civil-status codes, payment methods, banks, professional
specialties, etc.). Modelling each as its own canonical entity would
balloon the model without adding value: destination PMSs usually have
their own master tables for these.

Instead, we emit them all as ``CanonicalCatalogItem`` rows tagged with a
``kind`` so the destination can either merge by ``code`` against its own
master table, or import them as-is.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CatalogKind(StrEnum):
    COUNTRY = "country"
    PROVINCE = "province"
    CITY = "city"
    CIVIL_STATUS = "civil_status"
    TITLE = "title"
    PROFESSION = "profession"
    SPECIALTY = "specialty"
    REFERRAL_SOURCE = "referral_source"
    PAYMENT_METHOD = "payment_method"
    BANK = "bank"
    APPOINTMENT_STATUS = "appointment_status"
    CHAIR = "chair"
    RECALL_REASON = "recall_reason"
    RECALL_OUTCOME = "recall_outcome"
    ICON = "icon"
    OTHER = "other"


class CanonicalCatalogItem(BaseCanonicalEntity):
    """A single entry in a reference/lookup table."""

    entity_type: str = Field(default="catalog_item", frozen=True)

    kind: CatalogKind
    code: str | None = Field(
        default=None,
        description="Short code or alphanumeric key carried by the source row.",
    )
    name: str | None = Field(
        default=None,
        description="Human-readable label for the entry.",
    )
    description: str | None = None
    parent_uuid: UUID | None = Field(
        default=None,
        description=(
            "Set when the catalog has a hierarchy (e.g. province belongs to "
            "country, city belongs to province). Resolved deterministically."
        ),
    )

    tenant_label: str | None = None
