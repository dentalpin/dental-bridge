"""Transform Gesdén ``PagoCli`` rows into :class:`CanonicalPayment`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.payment import CanonicalPayment


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _resolve_catalog(ctx: TransformContext, kind: str, source_id: object | None):
    if source_id in (None, "", 0):
        return None
    return derive_canonical_uuid(ctx.source_system, "catalog_item", f"{kind}:{source_id}")


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPayment:
    source_id = str(row["IdPagoCli"])
    return CanonicalPayment(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "payment", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        bank_uuid=_resolve_catalog(ctx, "bank", row.get("IdBanco")),
        payment_method_uuid=_resolve_catalog(ctx, "payment_method", row.get("IdForPago")),
        user_uuid=_resolve(ctx, "user", row.get("IdUser")),
        applied_treatment_uuid=_resolve(ctx, "applied_treatment", row.get("IdentTM")),
        cancelled_by_uuid=_resolve(ctx, "payment", row.get("IdAnulado")),
        related_payment_uuid=_resolve(ctx, "payment", row.get("IdPagoCliRelacionado")),
        amount=coerce_decimal(row.get("Pagado")),
        paid_on=clean_date(row.get("FecPago")),
        payment_kind=coerce_int(row.get("Tipo")),
        receipt_number=normalise_string(row.get("NRecibo")),
        deposit_number=normalise_string(row.get("NumIngre")),
        invoice_number=normalise_string(row.get("NFactura")),
        iban=normalise_string(row.get("CodIBAN")),
        transaction_number=(
            str(row["NumTransaccion"]) if row.get("NumTransaccion") not in (None, "") else None
        ),
        return_transaction_number=(
            str(row["IdDevolucionTransaccion"])
            if row.get("IdDevolucionTransaccion") not in (None, "")
            else None
        ),
        payment_gateway_id=(
            str(row["IdPasarelaPago"]) if row.get("IdPasarelaPago") not in (None, "") else None
        ),
        bank_remittance_id=(
            str(row["IdRemesaBancaria"]) if row.get("IdRemesaBancaria") not in (None, "") else None
        ),
        automatic=_bool(row.get("Automatico")),
        available=not _bool(row.get("NoDisponible")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
