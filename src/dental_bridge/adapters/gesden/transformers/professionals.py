"""Transform a Gesdén ``TColabos`` row into :class:`CanonicalProfessional`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_national_id,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.professional import (
    CanonicalProfessional,
    ProfessionalRole,
)

# Gesdén's IdTipoColab is a small integer with site-specific semantics.
# The mapping below is a best-effort default; clinics with custom
# IdTipoColab values can override via a future configuration file.
_DEFAULT_ROLE_MAP: dict[int, ProfessionalRole] = {
    1: ProfessionalRole.DOCTOR,
    2: ProfessionalRole.HYGIENIST,
    3: ProfessionalRole.AUXILIARY,
    4: ProfessionalRole.ADMIN,
}


def _decode_role(value: object | None) -> ProfessionalRole:
    if value is None:
        return ProfessionalRole.OTHER
    try:
        return _DEFAULT_ROLE_MAP.get(int(value), ProfessionalRole.OTHER)
    except (TypeError, ValueError):
        return ProfessionalRole.OTHER


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalProfessional:
    source_id = str(row["IdCol"])
    return CanonicalProfessional(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "professional", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        code=normalise_string(row.get("Codigo")),
        given_name=normalise_string(row.get("Nombre")),
        family_name=normalise_string(row.get("Apellidos")),
        national_id=normalise_national_id(row.get("NIF")),
        role=_decode_role(row.get("IdTipoColab")),
    )
