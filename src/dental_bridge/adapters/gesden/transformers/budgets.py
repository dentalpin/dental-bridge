"""Transform Gesdén ``Presu`` rows into :class:`CanonicalBudget`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.budget import CanonicalBudget


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalBudget:
    source_id = str(row["Ident"])
    return CanonicalBudget(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "budget", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        elaborated_by_user_uuid=_resolve(ctx, "user", row.get("IdUserElabora")),
        presented_by_user_uuid=_resolve(ctx, "user", row.get("IdUserPresentacion")),
        rejected_by_user_uuid=_resolve(ctx, "user", row.get("Id_UserRechaz")),
        series_number=coerce_int(row.get("NumSerie")),
        number=coerce_int(row.get("NumPre")),
        title=normalise_string(row.get("Titulo")),
        notes=normalise_string(row.get("Notas")),
        quote_date=clean_date(row.get("FecPresup")),
        accepted_date=clean_date(row.get("FecAcepta")),
        rejected_date=clean_date(row.get("FecRechaz")),
        rejection_observations=normalise_string(row.get("ObsRechaz")),
        status_code=coerce_int(row.get("Estado")),
        is_alternative=bool(row.get("EsAlternativa"))
        if row.get("EsAlternativa") is not None
        else False,
        alternative_of_uuid=_resolve(ctx, "budget", row.get("AlternativaDe")),
        original_budget_uuid=_resolve(ctx, "budget", row.get("Id_PresuOriginal")),
        legal_hash=normalise_string(row.get("Hash")),
        legal_hash_control=normalise_string(row.get("HashControl")),
        codigo_atcud=normalise_string(row.get("CodigoATCUD")),
        codigo_qr=normalise_string(row.get("CodigoQR")),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
