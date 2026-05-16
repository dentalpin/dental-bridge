"""CanonicalDebt + CanonicalDebtPaymentApplication.

A debt is the amount a client owes for an applied treatment phase
(typically) that has been billed. A debt-payment application is the
fact that some portion of a payment has been applied to a debt — the
many-to-many between payments and debts.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalDebt(BaseCanonicalEntity):
    """An amount owed by a client for an applied treatment."""

    entity_type: str = Field(default="debt", frozen=True)

    patient_uuid: UUID | None = None
    client_uuid: UUID | None = None
    center_uuid: UUID | None = None
    applied_treatment_uuid: UUID | None = Field(
        default=None,
        description="The treatment that generated this debt (IdentTM).",
    )
    cancelled_by_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: the cancellation row that voided this debt (IdAnulado).",
    )
    uncollectible_reason_uuid: UUID | None = None

    treatment_number: str | None = None
    phase_number: int | None = None

    due_date: date | None = None

    owed_amount: Decimal | None = None
    pending_amount: Decimal | None = None
    settled: bool = False
    uncollectible: bool = False
    uncollectible_description: str | None = None

    invoice_count: int | None = None
    invoice_number: str | None = None
    treatment_note_number: str | None = None
    modality: int | None = None

    tenant_label: str | None = None


class CanonicalDebtPaymentApplication(BaseCanonicalEntity):
    """One payment-to-debt allocation."""

    entity_type: str = Field(default="debt_payment_application", frozen=True)

    debt_uuid: UUID
    payment_uuid: UUID
    fiscal_document_uuid: UUID | None = Field(
        default=None,
        description="Document that materialised this allocation (IdDocAdminDeuda).",
    )

    amount_applied: Decimal | None = None
    applied_on: date | None = None
    edit_treatments_flag: bool = False
    sub_payment_type: int | None = None

    tenant_label: str | None = None
