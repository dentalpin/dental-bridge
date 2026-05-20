"""Transform a Gesdén ``TColabos`` or ``TUsuAgd`` row into :class:`CanonicalProfessional`.

The extractor unions both tables under a single query. Rows from
``TColabos`` carry an ``IdTipoColab`` numeric role; rows from
``TUsuAgd`` arrive with ``source_table='tusuagd'`` and a synthetic
``pk`` prefixed by ``usuagd:`` so canonical UUIDs from each source
never collide. ``DCitas.IdUsu`` resolves to the ``usuagd:<IdUsu>``
canonical UUID — see ``transformers/appointments.py``.
"""

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
    # `pk` is provided by the extractor's union query; for legacy
    # callers that still pass `IdCol` (e.g. existing unit tests), fall
    # back to the integer key so the transformer keeps working.
    source_id = str(row.get("pk") or row["IdCol"])
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
