"""CanonicalPayment — money received from a client.

Payments are *historical records*: the destination must never re-execute
the underlying bank transaction or payment-gateway charge. Transaction
identifiers (``NumTransaccion``, ``IdPasarelaPago``, ``IdRemesaBancaria``)
are preserved as opaque strings/uuids so the audit chain stays intact.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalPayment(BaseCanonicalEntity):
    """A payment received from a client."""

    entity_type: str = Field(default="payment", frozen=True)

    client_uuid: UUID | None = None
    center_uuid: UUID | None = None
    bank_uuid: UUID | None = Field(
        default=None,
        description="canonical_uuid of the Bancos catalog row.",
    )
    payment_method_uuid: UUID | None = Field(
        default=None,
        description="canonical_uuid of the TForPago catalog row.",
    )
    user_uuid: UUID | None = None
    applied_treatment_uuid: UUID | None = Field(
        default=None,
        description="When the payment is tied to a specific treatment (IdentTM).",
    )

    cancelled_by_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: the cancellation payment that voided this one (IdAnulado).",
    )
    related_payment_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: arbitrary related-payment link (IdPagoCliRelacionado).",
    )

    amount: Decimal | None = None
    paid_on: date | None = None

    payment_kind: int | None = Field(
        default=None,
        description="Source ``Tipo`` numeric code (cash, transfer, card, etc.).",
    )

    receipt_number: str | None = None
    deposit_number: str | None = None
    invoice_number: str | None = None
    iban: str | None = None

    transaction_number: str | None = None
    return_transaction_number: str | None = None
    payment_gateway_id: str | None = None
    bank_remittance_id: str | None = None

    automatic: bool = False
    available: bool = True

    tenant_label: str | None = None
