"""Transform Gesdén ``DeudaCli`` rows into :class:`CanonicalDebt`."""

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
from dental_bridge.core.canonical.debt import CanonicalDebt


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalDebt:
    source_id = str(row["IdDeudaCli"])
    return CanonicalDebt(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "debt", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        applied_treatment_uuid=_resolve(ctx, "applied_treatment", row.get("IdentTM")),
        cancelled_by_uuid=_resolve(ctx, "debt", row.get("IdAnulado")),
        uncollectible_reason_uuid=(
            derive_canonical_uuid(
                ctx.source_system,
                "catalog_item",
                f"uncollectible_reason:{row['IdMotivoIncobrable']}",
            )
            if row.get("IdMotivoIncobrable") not in (None, "", 0)
            else None
        ),
        treatment_number=normalise_string(row.get("NumTto")),
        phase_number=coerce_int(row.get("NumFase")),
        due_date=clean_date(row.get("FecPlazo")),
        owed_amount=coerce_decimal(row.get("Adeudo")),
        pending_amount=coerce_decimal(row.get("Pendiente")),
        settled=_bool(row.get("Liquidado")),
        uncollectible=_bool(row.get("Incobrable")),
        uncollectible_description=normalise_string(row.get("DescMotivoIncobrable")),
        invoice_count=coerce_int(row.get("Docs")),
        invoice_number=normalise_string(row.get("NFactura")),
        treatment_note_number=normalise_string(row.get("NNotaTto")),
        modality=coerce_int(row.get("Modalidad")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
