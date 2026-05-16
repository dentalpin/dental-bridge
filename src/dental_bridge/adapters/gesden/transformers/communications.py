"""Transform ``EdMail`` rows into :class:`CanonicalCommunication`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.clinical_secondary import CanonicalCommunication


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _coerce_dt(value: object | None) -> datetime | None:
    return value if isinstance(value, datetime) else None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalCommunication:
    source_id = str(row["IdRun"])
    return CanonicalCommunication(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "communication", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        user_uuid=_resolve(ctx, "user", row.get("IdUser")),
        center_uuid=_resolve(ctx, "center", row.get("IdCentro")),
        kind="email",
        sent_from=_coerce_dt(row.get("FecPrintI")),
        sent_to=_coerce_dt(row.get("FecPrintF")),
        document_reference=(str(row["IdDoc"]) if row.get("IdDoc") not in (None, "", 0) else None),
        notes=normalise_string(row.get("Notas")),
        filter_description=normalise_string(row.get("Filtro")),
    )
