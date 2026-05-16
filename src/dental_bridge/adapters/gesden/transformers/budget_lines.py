"""Transform Gesdén ``PresuTto`` rows into :class:`CanonicalBudgetLine`."""

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
from dental_bridge.core.canonical.budget import CanonicalBudgetLine

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


def _camel_to_snake(name: str) -> str:
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)


def _odontogram_dict(row: dict[str, Any]) -> dict[str, int | None]:
    return {_camel_to_snake(col): coerce_int(row.get(col)) for col in _ODONTOGRAM_COLUMNS}


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalBudgetLine:
    source_id = str(row["Ident"])
    return CanonicalBudgetLine(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "budget_line", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        budget_uuid=derive_canonical_uuid(ctx.source_system, "budget", str(row["Id_Presu"])),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        client_uuid=_resolve(ctx, "client", row.get("IdCli")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        auxiliary_professional_uuid=_resolve(ctx, "professional", row.get("IdColAux")),
        treatment_variant_uuid=_resolve(ctx, "treatment_catalog_variant", row.get("IdTto")),
        treatment_uuid=_resolve(ctx, "treatment_catalog_item", row.get("IdTratamiento")),
        applied_treatment_uuid=_resolve(ctx, "applied_treatment", row.get("IdTtoMedOrig")),
        line_number=coerce_int(row.get("LinPre")),
        order_within_budget=coerce_int(row.get("Orden")),
        status_code=coerce_int(row.get("StaTto")),
        units=coerce_decimal(row.get("Unidades")),
        unit_amount=coerce_decimal(row.get("ImporteUni")),
        list_amount=coerce_decimal(row.get("ImportePre")),
        discount_percent=coerce_decimal(row.get("Dto")),
        discount_amount=coerce_decimal(row.get("ImporteDto")),
        base_amount=coerce_decimal(row.get("BaseImponible")),
        vat_percent=coerce_decimal(row.get("TpcIVA")),
        vat_amount=coerce_decimal(row.get("ImporteIVA")),
        start_date=clean_date(row.get("FecIni")),
        end_date=clean_date(row.get("FecFin")),
        accepted_date=clean_date(row.get("FecAcepta")),
        notes=normalise_string(row.get("Notas")),
        time_units=coerce_int(row.get("Tiempo")),
        odontogram_raw=_odontogram_dict(row),
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
