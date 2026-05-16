"""Tests for the Sprint-5 financial transformers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.adapters.gesden.transformers.debt_payment_applications import (
    transform as transform_dpa,
)
from dental_bridge.adapters.gesden.transformers.debts import (
    transform as transform_debt,
)
from dental_bridge.adapters.gesden.transformers.fiscal_document_lines import (
    transform as transform_doc_line,
)
from dental_bridge.adapters.gesden.transformers.fiscal_documents import (
    transform as transform_doc,
)
from dental_bridge.adapters.gesden.transformers.payments import (
    transform as transform_payment,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


def _ctx() -> TransformContext:
    return TransformContext(
        source_system="gesden",
        adapter_version="0.0.1",
        id_mapping=IdMapping(),
        warnings=WarningRegistry(),
    )


def test_fiscal_document_preserves_legal_hashes() -> None:
    row = {
        "Ident": 9001,
        "Doc": "F",
        "Serie": "A",
        "NumDoc": 12345,
        "Anyo": 2026,
        "IdEmisor": 1,
        "IdSerieOficial": 1,
        "SerieOficial": "A",
        "NumDocOficial": 12345,
        "TipoDocumento": 1,
        "TipoFactura": 1,
        "FecDoc": date(2026, 3, 1),
        "IdCli": 50,
        "IdCliTutor": None,
        "IdUser": 10,
        "Nombre": "MARÍA",
        "Apellidos": "GARCÍA NUÑEZ",
        "RazonSocial": None,
        "NIF": "12345678z",
        "NIFTutor": None,
        "Direccion": "C/ Mayor 1",
        "CP": "28001",
        "IdMotivo": None,
        "IdDocAdminOrigen": None,
        "ConceptoG": "Honorarios",
        "Modelo": "F",
        "Abonado": 0,
        "Abono": 0,
        "Anulacion": 0,
        "Hash": "abc123def",
        "HashControl": "ctrl-xyz",
        "CodigoATCUD": "JFAK-12345",
        "CodigoQR": "A:..00.B:..",
        "NumTransaccion": None,
        "IdDevolucionTransaccion": None,
        "_origen": "gesden",
        "Guid_Tenant": "abc",
    }
    d = transform_doc(row, _ctx())
    assert d.client_uuid == derive_canonical_uuid("gesden", "client", "50")
    assert d.legal_hash == "abc123def"
    assert d.legal_hash_control == "ctrl-xyz"
    assert d.codigo_atcud == "JFAK-12345"
    assert d.codigo_qr == "A:..00.B:.."
    assert d.recipient_family_name == "GARCÍA NUÑEZ"
    assert d.recipient_national_id == "12345678Z"


def test_fiscal_document_self_fk_origin() -> None:
    row = _minimal_doc()
    row["IdDocAdminOrigen"] = 9000
    d = transform_doc(row, _ctx())
    assert d.origin_document_uuid == derive_canonical_uuid("gesden", "fiscal_document", "9000")


def test_fiscal_document_line_resolves_all_refs() -> None:
    row = {
        "IdLinAdmin": 1,
        "IdDocAdmin": 9001,
        "IdDeudaCli": 700,
        "IdPagoCli": 800,
        "IdDeudaPago": 900,
        "IdPac": 42,
        "identTM": 12345,  # lowercase d in source
        "NumLinea": 1,
        "Concepto": "Limpieza",
        "Importe": 120.0,
        "BaseImponible": 99.17,
        "IdTipoIVA": 1,
        "TpcIVA": 21.0,
        "ImporteIVA": 20.83,
        "Dto": 0,
        "ImporteDto": 0,
        "Actos": 1,
        "Abonado": 0,
        "Abono": 0,
        "Guid_Tenant": "abc",
    }
    line = transform_doc_line(row, _ctx())
    assert line.document_uuid == derive_canonical_uuid("gesden", "fiscal_document", "9001")
    assert line.debt_uuid == derive_canonical_uuid("gesden", "debt", "700")
    assert line.payment_uuid == derive_canonical_uuid("gesden", "payment", "800")
    assert line.debt_payment_application_uuid == derive_canonical_uuid(
        "gesden", "debt_payment_application", "900"
    )
    assert line.applied_treatment_uuid == derive_canonical_uuid(
        "gesden", "applied_treatment", "12345"
    )
    assert line.amount == Decimal("120.0")
    assert line.base_amount == Decimal("99.17")
    assert line.vat_percent == Decimal("21.0")


def test_payment_basic_mapping() -> None:
    row = {
        "IdPagoCli": 800,
        "IdCli": 50,
        "IdCentro": 1,
        "IdBanco": 3,
        "IdForPago": 2,
        "IdUser": 10,
        "IdAnulado": None,
        "IdPagoCliRelacionado": None,
        "IdentTM": 12345,
        "IdMotivo": None,
        "Pagado": 120.0,
        "FecPago": date(2026, 3, 5),
        "Tipo": 1,
        "NRecibo": "R-9000",
        "NumIngre": None,
        "NCPago": None,
        "NFactura": "F-12345",
        "CodIBAN": "ES12 3456 7890",
        "NumTransaccion": None,
        "IdDevolucionTransaccion": None,
        "IdPasarelaPago": None,
        "IdRemesaBancaria": None,
        "Automatico": 0,
        "NoDisponible": 0,
        "Guid_Tenant": "abc",
    }
    p = transform_payment(row, _ctx())
    assert p.amount == Decimal("120.0")
    assert p.paid_on == date(2026, 3, 5)
    assert p.receipt_number == "R-9000"
    assert p.applied_treatment_uuid == derive_canonical_uuid("gesden", "applied_treatment", "12345")
    assert p.payment_method_uuid == derive_canonical_uuid(
        "gesden", "catalog_item", "payment_method:2"
    )
    assert p.bank_uuid == derive_canonical_uuid("gesden", "catalog_item", "bank:3")
    assert p.iban == "ES12 3456 7890"
    assert p.automatic is False
    assert p.available is True


def test_payment_cancellation_self_fk() -> None:
    row = _minimal_payment()
    row["IdAnulado"] = 799
    p = transform_payment(row, _ctx())
    assert p.cancelled_by_uuid == derive_canonical_uuid("gesden", "payment", "799")


def test_debt_basic_mapping() -> None:
    row = {
        "IdDeudaCli": 700,
        "IdCli": 50,
        "IdPac": 42,
        "IdCentro": 1,
        "IdentTM": 12345,
        "IdAnulado": None,
        "IdMotivoIncobrable": None,
        "NumTto": "T-2026-001",
        "NumFase": 1,
        "FecPlazo": date(2026, 4, 1),
        "Adeudo": 120.0,
        "Pendiente": 0.0,
        "Liquidado": 1,
        "Incobrable": 0,
        "DescMotivoIncobrable": None,
        "Docs": 1,
        "NFactura": "F-12345",
        "NNotaTto": None,
        "Modalidad": 1,
        "Guid_Tenant": "abc",
    }
    d = transform_debt(row, _ctx())
    assert d.owed_amount == Decimal("120.0")
    assert d.pending_amount == Decimal("0.0")
    assert d.settled is True
    assert d.uncollectible is False
    assert d.applied_treatment_uuid == derive_canonical_uuid("gesden", "applied_treatment", "12345")


def test_debt_payment_application_links_both_sides() -> None:
    row = {
        "IdDeudaPago": 900,
        "IdDeudaCli": 700,
        "IdPagoCli": 800,
        "IdDocAdminDeuda": 9001,
        "Pagado": 120.0,
        "FecPago": date(2026, 3, 6),
        "FecExpoCP": None,
        "EditTtos": 0,
        "SubTipoPago": 1,
        "Guid_Tenant": "abc",
    }
    a = transform_dpa(row, _ctx())
    assert a.debt_uuid == derive_canonical_uuid("gesden", "debt", "700")
    assert a.payment_uuid == derive_canonical_uuid("gesden", "payment", "800")
    assert a.fiscal_document_uuid == derive_canonical_uuid("gesden", "fiscal_document", "9001")
    assert a.amount_applied == Decimal("120.0")


# Helpers --------------------------------------------------------------


def _minimal_doc() -> dict[str, object]:
    return {
        "Ident": 9001,
        "Doc": "F",
        "Serie": "A",
        "NumDoc": 1,
        "Anyo": 2026,
        "IdEmisor": 1,
        "IdSerieOficial": None,
        "SerieOficial": None,
        "NumDocOficial": None,
        "TipoDocumento": 1,
        "TipoFactura": 1,
        "FecDoc": date(2026, 3, 1),
        "IdCli": 50,
        "IdCliTutor": None,
        "IdUser": 10,
        "Nombre": None,
        "Apellidos": None,
        "RazonSocial": None,
        "NIF": None,
        "NIFTutor": None,
        "Direccion": None,
        "CP": None,
        "IdMotivo": None,
        "IdDocAdminOrigen": None,
        "ConceptoG": None,
        "Modelo": None,
        "Abonado": 0,
        "Abono": 0,
        "Anulacion": 0,
        "Hash": None,
        "HashControl": None,
        "CodigoATCUD": None,
        "CodigoQR": None,
        "NumTransaccion": None,
        "IdDevolucionTransaccion": None,
        "_origen": None,
        "Guid_Tenant": "abc",
    }


def _minimal_payment() -> dict[str, object]:
    return {
        "IdPagoCli": 800,
        "IdCli": 50,
        "IdCentro": 1,
        "IdBanco": None,
        "IdForPago": 1,
        "IdUser": 10,
        "IdAnulado": None,
        "IdPagoCliRelacionado": None,
        "IdentTM": None,
        "IdMotivo": None,
        "Pagado": 100.0,
        "FecPago": date(2026, 3, 5),
        "Tipo": 1,
        "NRecibo": None,
        "NumIngre": None,
        "NCPago": None,
        "NFactura": None,
        "CodIBAN": None,
        "NumTransaccion": None,
        "IdDevolucionTransaccion": None,
        "IdPasarelaPago": None,
        "IdRemesaBancaria": None,
        "Automatico": 0,
        "NoDisponible": 0,
        "Guid_Tenant": "abc",
    }
