"""Fiscal document mapping tests use synthetic invoice rows only."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.transformers.fiscal_documents import (
    transform_document,
    transform_document_line,
)
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _context() -> TransformContext:
    return TransformContext(
        source_system="nemodent",
        adapter_version="0.1.0",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
        tenant_label="fixture",
    )


def test_invoice_header_maps_identity_numbering_and_date() -> None:
    context = _context()

    document = transform_document(
        {
            "GUID": "invoice-1",
            "GUID_HOLDER_ACCOUNT": "account-1",
            "Date": date(2025, 6, 7),
            "DocumentType": 2,
            "InvoiceNumber": "00042",
            "SerieID": "A",
            "Name": "Fixture Recipient",
            "NIF": "X123",
            "Address": "Fixture street",
            "ZipCode": "00001",
            "Total": Decimal("55.00"),
        },
        context,
    )

    assert document is not None
    assert document.source_id == "invoice-1"
    assert document.series == "A"
    assert document.number == "00042"
    assert document.document_type == 2
    assert document.document_date == date(2025, 6, 7)
    assert document.recipient_legal_name == "Fixture Recipient"
    assert document.recipient_national_id == "X123"
    assert document.raw_source_data["Name"] == "Fixture Recipient"


def test_invoice_line_maps_total_base_units_and_vat() -> None:
    context = _context()
    document = transform_document(
        {"GUID": "invoice-1", "Date": date(2025, 6, 7)},
        context,
    )
    assert document is not None
    context.id_mapping.register("nemodent", "fiscal_document", document.source_id)

    line = transform_document_line(
        {
            "GUID": "invoice-line-1",
            "GUID_HEADING": "invoice-1",
            "Class": "1",
            "ProcedureID": "P1",
            "Description": "Synthetic item",
            "Quantity": 2,
            "Amount": Decimal("25.00"),
            "TotalAmount": Decimal("55.00"),
            "VAT": Decimal("10"),
        },
        context,
    )

    assert line is not None
    assert line.document_uuid == document.canonical_uuid
    assert line.concept == "Synthetic item"
    assert line.units == 2
    assert line.amount == Decimal("55.00")
    assert line.base_amount == Decimal("50.00")
    assert line.vat_percent == Decimal("10")


def test_invoice_line_without_exported_header_is_omitted() -> None:
    context = _context()

    line = transform_document_line(
        {"GUID": "orphan-line", "GUID_HEADING": "missing-invoice"},
        context,
    )

    assert line is None
    assert [warning.code for warning in context.warnings] == [
        "fiscal_document_line.document_unresolved"
    ]
