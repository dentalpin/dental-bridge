"""Transform ``TConsinCab`` rows into :class:`CanonicalConsent`.

Only the rendered text/html is migrated. The ``TConsinDet`` key-value
detail rows are intentionally skipped — they reference template files
not present in the database, so the decomposition is not reconstructable
on its own.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.adapters.gesden.transformers._money import coerce_int
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.clinical_secondary import CanonicalConsent


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _coerce_dt(value: object | None) -> datetime | None:
    return value if isinstance(value, datetime) else None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalConsent:
    source_id = str(row["IdConsin"])
    return CanonicalConsent(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "consent", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPac"])),
        professional_uuid=_resolve(ctx, "professional", row.get("IdCol")),
        signed_by_user_uuid=_resolve(ctx, "user", row.get("FirmaIdUsu")),
        signed_by_professional_uuid=_resolve(ctx, "professional", row.get("IdColFirma")),
        title=normalise_string(row.get("Titulo")),
        representative=normalise_string(row.get("Representante")),
        doctor_name=normalise_string(row.get("Doctor")),
        college_number=normalise_string(row.get("NumColegiado")),
        rendered_text=normalise_string(row.get("Texto")),
        rendered_html=normalise_string(row.get("Html")),
        generated_on=_coerce_dt(row.get("FechaGen")),
        signed_on=_coerce_dt(row.get("FechaFirma")),
        print_count=coerce_int(row.get("NumImp")),
        signed=bool(row.get("Firmado")) if row.get("Firmado") is not None else False,
    )
