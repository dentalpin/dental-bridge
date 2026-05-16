"""Transform a Gesdén ``TUsers`` row into :class:`CanonicalUser`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.user import CanonicalUser


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalUser:
    source_id = str(row["IdUser"])

    professional_uuid = None
    pro_raw = row.get("IdCol")
    if pro_raw not in (None, "", 0):
        professional_uuid = derive_canonical_uuid(ctx.source_system, "professional", str(pro_raw))

    return CanonicalUser(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "user", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        login=normalise_string(row.get("Login")),
        given_name=normalise_string(row.get("Nombre")),
        family_name=normalise_string(row.get("Apellidos")),
        professional_uuid=professional_uuid,
    )
