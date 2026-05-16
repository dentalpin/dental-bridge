"""Transform Gesdén ``DocAdmin`` rows into :class:`CanonicalFiscalDocument`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_national_id,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.fiscal_document import CanonicalFiscalDocument


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalFiscalDocument:
    source_id = str(row["Ident"])
    return CanonicalFiscalDocument(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "fiscal_document", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        guardian_client_uuid=_resolve(ctx, "client", row.get("IdCliTutor")),
        user_uuid=_resolve(ctx, "user", row.get("IdUser")),
        origin_document_uuid=_resolve(ctx, "fiscal_document", row.get("IdDocAdminOrigen")),
        document_kind=normalise_string(row.get("Doc")),
        series=normalise_string(row.get("Serie")),
        number=normalise_string(str(row.get("NumDoc"))) if row.get("NumDoc") is not None else None,
        year=coerce_int(row.get("Anyo")),
        official_series=normalise_string(row.get("SerieOficial")),
        official_number=(
            normalise_string(str(row.get("NumDocOficial")))
            if row.get("NumDocOficial") is not None
            else None
        ),
        document_type=coerce_int(row.get("TipoDocumento")),
        invoice_type=coerce_int(row.get("TipoFactura")),
        document_date=clean_date(row.get("FecDoc")),
        recipient_given_name=normalise_string(row.get("Nombre")),
        recipient_family_name=normalise_string(row.get("Apellidos")),
        recipient_legal_name=normalise_string(row.get("RazonSocial")),
        recipient_national_id=normalise_national_id(row.get("NIF")),
        recipient_address=normalise_string(row.get("Direccion")),
        recipient_postal_code=normalise_string(row.get("CP")),
        recipient_guardian_national_id=normalise_national_id(row.get("NIFTutor")),
        refunded=_bool(row.get("Abonado")),
        is_refund=_bool(row.get("Abono")),
        cancellation_flag=_bool(row.get("Anulacion")),
        concept=normalise_string(row.get("ConceptoG")),
        model=normalise_string(row.get("Modelo")),
        legal_hash=normalise_string(row.get("Hash")),
        legal_hash_control=normalise_string(row.get("HashControl")),
        codigo_atcud=normalise_string(row.get("CodigoATCUD")),
        codigo_qr=normalise_string(row.get("CodigoQR")),
        transaction_number=(
            str(row["NumTransaccion"]) if row.get("NumTransaccion") not in (None, "") else None
        ),
        return_transaction_number=(
            str(row["IdDevolucionTransaccion"])
            if row.get("IdDevolucionTransaccion") not in (None, "")
            else None
        ),
        origin_label=normalise_string(row.get("_origen")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
