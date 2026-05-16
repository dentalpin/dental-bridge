"""Transform a Gesdén ``Centros`` row into :class:`CanonicalCenter`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.center import CanonicalCenter


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalCenter:
    source_id = str(row["IdCentro"])
    return CanonicalCenter(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "center", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        code=normalise_string(row.get("CodCentro")),
        name=normalise_string(row.get("Descripcio")),
    )
