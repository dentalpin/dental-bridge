"""Transform Nemodent invoice headers and lines into DPMF fiscal documents."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import (
    FISCAL_DOCUMENT_COLUMNS,
    FISCAL_DOCUMENT_LINE_COLUMNS,
)
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    as_date,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.fiscal_document import (
    CanonicalFiscalDocument,
    CanonicalFiscalDocumentLine,
)


def transform_document(
    row: dict[str, Any], context: TransformContext
) -> CanonicalFiscalDocument | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="fiscal_document.missing_source_id",
            message="Nemodent invoice has no GUID and was omitted.",
            entity_type="fiscal_document",
        )
        return None

    return CanonicalFiscalDocument(
        **canonical_envelope(
            context,
            "fiscal_document",
            source_id,
            {key: row.get(key) for key in FISCAL_DOCUMENT_COLUMNS},
        ),
        series=text(row.get("SerieID")),
        number=text(row.get("InvoiceNumber")),
        document_type=_optional_int(row.get("DocumentType")),
        document_date=as_date(row.get("Date")),
        recipient_legal_name=text(row.get("Name")),
        recipient_national_id=text(row.get("NIF")),
        recipient_address=text(row.get("Address")),
        recipient_postal_code=text(row.get("ZipCode")),
        tenant_label=context.tenant_label,
    )


def transform_document_line(
    row: dict[str, Any], context: TransformContext
) -> CanonicalFiscalDocumentLine | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="fiscal_document_line.missing_source_id",
            message="Nemodent invoice line has no GUID and was omitted.",
            entity_type="fiscal_document_line",
        )
        return None

    document_source_id = text(row.get("GUID_HEADING"))
    document_uuid = (
        context.id_mapping.resolve(
            context.source_system,
            "fiscal_document",
            document_source_id,
            require_known=True,
        )
        if document_source_id is not None
        else None
    )
    if document_uuid is None:
        context.warnings.add(
            severity="error",
            code="fiscal_document_line.document_unresolved",
            message="Nemodent invoice line has no exported parent document and was omitted.",
            entity_type="fiscal_document_line",
            source_id=source_id,
        )
        return None

    quantity = _optional_int(row.get("Quantity"))
    unit_amount = _decimal(row.get("Amount"))
    base_amount = (
        unit_amount * quantity if unit_amount is not None and quantity is not None else None
    )
    return CanonicalFiscalDocumentLine(
        **canonical_envelope(
            context,
            "fiscal_document_line",
            source_id,
            {key: row.get(key) for key in FISCAL_DOCUMENT_LINE_COLUMNS},
        ),
        document_uuid=document_uuid,
        line_number=None,
        concept=text(row.get("Description")),
        amount=_decimal(row.get("TotalAmount")),
        base_amount=base_amount,
        vat_percent=_decimal(row.get("VAT")),
        units=quantity,
        tenant_label=context.tenant_label,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if number != number.to_integral_value():
        return None
    return int(number)


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
