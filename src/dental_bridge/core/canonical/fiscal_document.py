"""Canonical entities for invoices, receipts and credit notes.

Gesdén keeps every legally-issued document in ``DocAdmin``, with line
detail in ``LinAdmin``. These rows are treated as **immutable historical
records** — their legal hashes (Hash, HashControl, CodigoATCUD, CodigoQR)
must round-trip verbatim. Destination importers MUST NOT re-sign or
renumber them; the chain of legal series is preserved as-is so a
follow-up audit can reconstruct it.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalFiscalDocument(BaseCanonicalEntity):
    """A legal commercial document (invoice, receipt, credit note)."""

    entity_type: str = Field(default="fiscal_document", frozen=True)

    # References ----------------------------------------------------------
    client_uuid: UUID | None = None
    guardian_client_uuid: UUID | None = Field(
        default=None,
        description="Tutor/legal guardian for minor-patient documents (IdCliTutor).",
    )
    user_uuid: UUID | None = None
    origin_document_uuid: UUID | None = Field(
        default=None,
        description=(
            "Self-FK: the original document this one cancels or amends "
            "(IdDocAdminOrigen). Chain of legal corrections."
        ),
    )

    # Numbering & series --------------------------------------------------
    document_kind: str | None = Field(
        default=None,
        description="Source ``Doc`` value (F, FR, A, AR, …) identifying the document family.",
    )
    series: str | None = None
    number: str | None = None
    year: int | None = None
    official_series: str | None = None
    official_number: str | None = None
    document_type: int | None = None
    invoice_type: int | None = None

    # Dates --------------------------------------------------------------
    document_date: date | None = None

    # Recipient denormalised (preserved as-issued for legal exactness) ----
    recipient_given_name: str | None = None
    recipient_family_name: str | None = None
    recipient_legal_name: str | None = None
    recipient_national_id: str | None = None
    recipient_address: str | None = None
    recipient_postal_code: str | None = None
    recipient_guardian_national_id: str | None = None

    # Amounts / lifecycle flags ------------------------------------------
    refunded: bool = False
    is_refund: bool = False
    cancellation_flag: bool = False
    concept: str | None = None
    model: str | None = None

    # Legal hashes (verbatim, never re-signed) ----------------------------
    legal_hash: str | None = None
    legal_hash_control: str | None = None
    codigo_atcud: str | None = None
    codigo_qr: str | None = None

    # Transaction references ---------------------------------------------
    transaction_number: str | None = None
    return_transaction_number: str | None = None

    origin_label: str | None = Field(
        default=None,
        description="Source ``_origen`` column — system that originated the document.",
    )

    tenant_label: str | None = None


class CanonicalFiscalDocumentLine(BaseCanonicalEntity):
    """A single concept line within a :class:`CanonicalFiscalDocument`."""

    entity_type: str = Field(default="fiscal_document_line", frozen=True)

    document_uuid: UUID
    debt_uuid: UUID | None = None
    payment_uuid: UUID | None = None
    debt_payment_application_uuid: UUID | None = None
    patient_uuid: UUID | None = None
    applied_treatment_uuid: UUID | None = Field(
        default=None,
        description="When the line bills a specific treatment (LinAdmin.identTM).",
    )

    line_number: int | None = None
    concept: str | None = None

    amount: Decimal | None = None
    base_amount: Decimal | None = None
    vat_type_code: int | None = None
    vat_percent: Decimal | None = None
    vat_amount: Decimal | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None

    units: int | None = None
    refunded: bool = False
    is_refund: bool = False

    tenant_label: str | None = None
