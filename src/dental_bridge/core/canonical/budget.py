"""Canonical entities for budgets/quotes (``Presu`` + ``PresuTto``)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalBudget(BaseCanonicalEntity):
    """A quotation/budget offered to a patient."""

    entity_type: str = Field(default="budget", frozen=True)

    patient_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    center_uuid: UUID | None = None
    elaborated_by_user_uuid: UUID | None = None
    presented_by_user_uuid: UUID | None = None
    rejected_by_user_uuid: UUID | None = None

    series_number: int | None = None
    number: int | None = None
    title: str | None = None
    notes: str | None = None

    quote_date: date | None = None
    accepted_date: date | None = None
    rejected_date: date | None = None
    rejection_observations: str | None = None

    status_code: int | None = None
    is_alternative: bool = False
    alternative_of_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: the budget this one is an alternative of (AlternativaDe).",
    )
    original_budget_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: the budget this one was cloned/derived from (Id_PresuOriginal).",
    )

    # Legal/fiscal hashes preserved verbatim — never re-signed downstream.
    legal_hash: str | None = None
    legal_hash_control: str | None = None
    codigo_atcud: str | None = None
    codigo_qr: str | None = None

    tenant_label: str | None = None


class CanonicalBudgetLine(BaseCanonicalEntity):
    """One line of a :class:`CanonicalBudget`."""

    entity_type: str = Field(default="budget_line", frozen=True)

    budget_uuid: UUID
    patient_uuid: UUID | None = None
    client_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    auxiliary_professional_uuid: UUID | None = None
    treatment_variant_uuid: UUID | None = None
    treatment_uuid: UUID | None = None
    applied_treatment_uuid: UUID | None = Field(
        default=None,
        description=(
            "Forms the forward half of the Presu↔TtosMed double link "
            "(``IdTtoMedOrig`` in the source row)."
        ),
    )

    line_number: int | None = None
    order_within_budget: int | None = None
    status_code: int | None = None

    units: Decimal | None = None
    unit_amount: Decimal | None = None
    list_amount: Decimal | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None
    base_amount: Decimal | None = None
    vat_percent: Decimal | None = None
    vat_amount: Decimal | None = None

    start_date: date | None = None
    end_date: date | None = None
    accepted_date: date | None = None

    notes: str | None = None
    time_units: int | None = None

    # Odontogram raw (same handling as AppliedTreatment).
    odontogram_raw: dict[str, int | None] = Field(default_factory=dict)

    tenant_label: str | None = None
