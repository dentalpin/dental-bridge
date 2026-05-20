"""Transform Gesdén ``TtosMed`` rows into :class:`CanonicalAppliedTreatment`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dental_bridge.adapters.gesden.decoders.odontogram import (
    decode_piezas_adu,
    decode_piezas_lec,
)
from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_decimal, coerce_int
from dental_bridge.core.canonical.applied_treatment import CanonicalAppliedTreatment
from dental_bridge.core.canonical.base import derive_canonical_uuid

# The Gesdén odontogram is encoded across these source columns. We
# preserve them as opaque integers; decoding is deferred to a later
# sprint pending UI validation (see docs/odontograma_decoding.md).
_ODONTOGRAM_COLUMNS = (
    "ZonasBoca",
    "PiezasAdu",
    "PiezasLec",
    "PiezasNum",
    "ZonasPieza",
    "IdTipoOdg",
    "Cuadrantes",
    "Arcadas",
    "DespX",
    "DespY",
    "Rotacion",
)


def _odontogram_dict(row: dict[str, Any]) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for source_col in _ODONTOGRAM_COLUMNS:
        value = row.get(source_col)
        out[_camel_to_snake(source_col)] = coerce_int(value)
    return out


def _camel_to_snake(name: str) -> str:
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _coerce_datetime(value: object | None) -> datetime | None:
    return value if isinstance(value, datetime) else None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalAppliedTreatment:
    source_id = str(row["Ident"])
    return CanonicalAppliedTreatment(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "applied_treatment", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        auxiliary_professional_uuid=_resolve(ctx, "professional", row.get("IdColAux")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        treatment_variant_uuid=_resolve(ctx, "treatment_catalog_variant", row.get("IdTto")),
        user_uuid=_resolve(ctx, "user", row.get("IdUser")),
        budget_line_uuid=_resolve(ctx, "budget_line", row.get("IdPresuTto")),
        referral_source_uuid=(
            derive_canonical_uuid(
                ctx.source_system, "catalog_item", f"referral_source:{row['IdRef']}"
            )
            if row.get("IdRef") not in (None, "", 0)
            else None
        ),
        treatment_number=normalise_string(row.get("NumTto")),
        status_code=coerce_int(row.get("StaTto")),
        start_date=clean_date(row.get("FecIni")),
        end_date=clean_date(row.get("FecFin")),
        expiry_date=clean_date(row.get("FechaCaduc")),
        validated_at=_coerce_datetime(row.get("FechaValida")),
        amount=coerce_decimal(row.get("Importe")),
        discount_percent=coerce_decimal(row.get("Dto")),
        discount_amount=coerce_decimal(row.get("ImporteDto")),
        pending_amount=coerce_decimal(row.get("Pendiente")),
        private_amount=coerce_decimal(row.get("ImportePrivado")),
        mutua_amount=coerce_decimal(row.get("ImporteMutua")),
        units=coerce_int(row.get("Actos")),
        sessions_performed=coerce_int(row.get("SesRealiz")),
        notes=normalise_string(row.get("Notas")),
        odontogram_raw=_odontogram_dict(row),
        teeth=decode_piezas_adu(row.get("PiezasAdu")) + decode_piezas_lec(row.get("PiezasLec")),
        document_number=normalise_string(row.get("NumDocUnico")),
        transaction_number=(
            str(row["NumTransaccion"]) if row.get("NumTransaccion") not in (None, "") else None
        ),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
