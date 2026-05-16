"""Canonical entities for the treatment catalog (templates).

Two source tables map here:

- ``Tratamientos`` — the master catalogue of treatments offered.
- ``Tratamientos_Tarifas`` — per-tariff variants (different code, price
  context, validity) of the same master treatment.

We keep both in canonical form so the destination importer can pick the
modelling that fits it. ``CanonicalTreatmentPhaseTemplate`` covers the
clinical-phase structure that templates can declare (``TratamientosFases``).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalTreatmentCatalogItem(BaseCanonicalEntity):
    """A treatment offered by the clinic (template, not yet applied)."""

    entity_type: str = Field(default="treatment_catalog_item", frozen=True)

    code: str | None = None
    short_name: str | None = None
    description: str | None = None
    patient_facing_description: str | None = None
    agenda_description: str | None = None
    specialty_uuid: UUID | None = None
    odontogram_kind_uuid: UUID | None = Field(
        default=None,
        description="canonical_uuid of the TTipoOdg catalog row, when set.",
    )
    duration_minutes: int | None = None
    number_of_phases: int | None = None
    reference_price: Decimal | None = None
    deactivated: bool = False
    valid_from: date | None = None
    valid_until: date | None = None
    tenant_label: str | None = None


class CanonicalTreatmentCatalogVariant(BaseCanonicalEntity):
    """A per-tariff variant of a :class:`CanonicalTreatmentCatalogItem`.

    Gesdén supports multiple tariff lists (insurance schemes, private,
    mutua) and each treatment template can carry a variant per tariff
    with its own code and price metadata.
    """

    entity_type: str = Field(default="treatment_catalog_variant", frozen=True)

    treatment_uuid: UUID
    tariff_code: str | None = Field(
        default=None,
        description="Source-system tariff identifier (IdTarifa). String form.",
    )
    code: str | None = None
    specialty_uuid: UUID | None = None
    deactivated: bool = False
    tenant_label: str | None = None


class CanonicalTreatmentPhaseTemplate(BaseCanonicalEntity):
    """A phase declared by a treatment template (``TratamientosFases``)."""

    entity_type: str = Field(default="treatment_phase_template", frozen=True)

    treatment_uuid: UUID
    description: str | None = None
    observations: str | None = None
    duration_minutes: int | None = None
    execution_order: int | None = None
    percent_to_bill: Decimal | None = None
    min_days: int | None = None
    max_days: int | None = None
    tenant_label: str | None = None
