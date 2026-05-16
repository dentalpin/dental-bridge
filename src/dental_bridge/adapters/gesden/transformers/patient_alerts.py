"""Transform ``AlertPac`` rows into :class:`CanonicalPatientAlert`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.clinical_secondary import CanonicalPatientAlert


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPatientAlert:
    source_id = str(row["Id"])
    return CanonicalPatientAlert(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "patient_alert", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPac"])),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        alert_number=coerce_int(row.get("NumAlerta")),
        text=normalise_string(row.get("Texto")),
        flagged=bool(row.get("Marcado")) if row.get("Marcado") is not None else False,
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
