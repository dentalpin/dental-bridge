"""Transform ``TDocumentosPac`` rows into :class:`CanonicalPatientDocument`.

In addition to producing the canonical entity, the transformer collects
a side-effect: a ``_files`` manifest entry pointing at the original
filename. The writer reads this via :meth:`DpmfWriter.append_file_ref`.
We expose the file-ref intent via the context's manifest queue so the
adapter can flush it after each row.
"""

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
from dental_bridge.core.canonical.clinical_secondary import CanonicalPatientDocument


def _resolve(ctx: TransformContext, entity_type: str, source_id: object | None):
    if source_id in (None, "", 0, -1):
        return None
    return derive_canonical_uuid(ctx.source_system, entity_type, str(source_id))


def _coerce_dt(value: object | None) -> datetime | None:
    return value if isinstance(value, datetime) else None


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPatientDocument:
    source_id = str(row["IdDocPac"])
    return CanonicalPatientDocument(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "patient_document", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", str(row["IdPac"])),
        user_uuid=_resolve(ctx, "user", row.get("IdUsu")),
        signed_by_user_uuid=_resolve(ctx, "user", row.get("FirmaIdUsu")),
        document_date=clean_date(row.get("FechaDoc")),
        inserted_on=_coerce_dt(row.get("FechaIns")),
        description=normalise_string(row.get("Descripcion")),
        notes=normalise_string(row.get("Notas")),
        original_filename=normalise_string(row.get("Original")),
        document_kind=coerce_int(row.get("TipoDoc")),
        signed=bool(row.get("Firmado")) if row.get("Firmado") is not None else False,
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )
