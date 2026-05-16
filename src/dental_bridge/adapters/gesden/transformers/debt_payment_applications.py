"""Transform Gesdén ``DeudaPago`` rows into :class:`CanonicalDebtPaymentApplication`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.debt import CanonicalDebtPaymentApplication


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalDebtPaymentApplication:
    source_id = str(row["IdDeudaPago"])
    return CanonicalDebtPaymentApplication(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "debt_payment_application", source_id
        ),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        debt_uuid=derive_canonical_uuid(ctx.source_system, "debt", str(row["IdDeudaCli"])),
        payment_uuid=derive_canonical_uuid(ctx.source_system, "payment", str(row["IdPagoCli"])),
        fiscal_document_uuid=_resolve(ctx, "fiscal_document", row.get("IdDocAdminDeuda")),
        amount_applied=coerce_decimal(row.get("Pagado")),
        applied_on=clean_date(row.get("FecPago")),
        edit_treatments_flag=_bool(row.get("EditTtos")),
        sub_payment_type=coerce_int(row.get("SubTipoPago")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
