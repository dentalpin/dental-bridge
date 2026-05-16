"""Transform ``RecetasCab`` rows into :class:`CanonicalPrescription`."""

from __future__ import annotations

from datetime import datetime
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
from dental_bridge.core.canonical.clinical_secondary import CanonicalPrescription


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _coerce_dt(value: object | None) -> datetime | None:
    return value if isinstance(value, datetime) else None


def _bool(value: object | None) -> bool:
    return bool(value) if value is not None else False


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPrescription:
    source_id = str(row["IdRecetaIdent"])
    return CanonicalPrescription(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "prescription", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=_resolve(ctx, "patient", row.get("IdPac")),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        issued_on=clean_date(row.get("Fecha")),
        inserted_on=_coerce_dt(row.get("FecIns")),
        printed_on=_coerce_dt(row.get("FechaImpresion")),
        description=normalise_string(row.get("Descripcio")),
        notes=normalise_string(row.get("Notas")),
        pharmacist_notes=normalise_string(row.get("NotasFarmaceutico")),
        diagnosis=normalise_string(row.get("Diagnostico")),
        prescription_kind=coerce_int(row.get("TipoReceta")),
        cve=normalise_string(row.get("CVE")),
        dispensed=_bool(row.get("Dispensada")),
        print_count=coerce_int(row.get("NumImpresiones")),
        cancelled=_bool(row.get("Anulada")),
        public=bool(row.get("Publico")) if row.get("Publico") is not None else None,
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
