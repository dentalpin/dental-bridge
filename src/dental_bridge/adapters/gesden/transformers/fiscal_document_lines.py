"""Transform Gesdén ``LinAdmin`` rows into :class:`CanonicalFiscalDocumentLine`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.fiscal_document import CanonicalFiscalDocumentLine


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalFiscalDocumentLine:
    source_id = str(row["IdLinAdmin"])
    return CanonicalFiscalDocumentLine(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "fiscal_document_line", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        document_uuid=derive_canonical_uuid(
            ctx.source_system, "fiscal_document", str(row["IdDocAdmin"])
        ),
        debt_uuid=_resolve(ctx, "debt", row.get("IdDeudaCli")),
        payment_uuid=_resolve(ctx, "payment", row.get("IdPagoCli")),
        debt_payment_application_uuid=_resolve(
            ctx, "debt_payment_application", row.get("IdDeudaPago")
        ),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        applied_treatment_uuid=_resolve(ctx, "applied_treatment", row.get("identTM")),
        line_number=coerce_int(row.get("NumLinea")),
        concept=normalise_string(row.get("Concepto")),
        amount=coerce_decimal(row.get("Importe")),
        base_amount=coerce_decimal(row.get("BaseImponible")),
        vat_type_code=coerce_int(row.get("IdTipoIVA")),
        vat_percent=coerce_decimal(row.get("TpcIVA")),
        vat_amount=coerce_decimal(row.get("ImporteIVA")),
        discount_percent=coerce_decimal(row.get("Dto")),
        discount_amount=coerce_decimal(row.get("ImporteDto")),
        units=coerce_int(row.get("Actos")),
        refunded=_bool(row.get("Abonado")),
        is_refund=_bool(row.get("Abono")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
