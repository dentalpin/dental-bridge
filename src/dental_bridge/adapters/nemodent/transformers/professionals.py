"""Transform Nemodent personnel without importing login credentials."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import PROFESSIONAL_COLUMNS
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    canonical_envelope,
    text,
    warn_once,
)
from dental_bridge.core.canonical.professional import (
    CanonicalProfessional,
    ProfessionalRole,
)


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalProfessional | None:
    source_id = text(row.get("ID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="professional.missing_source_id",
            message="Nemodent personnel row has no ID and was omitted.",
            entity_type="professional",
        )
        return None

    role_code = text(row.get("Type"))
    if role_code is not None:
        warn_once(
            context,
            f"professional.role_unmapped:{role_code}",
            severity="info",
            code="professional.role_unmapped",
            message="Nemodent personnel type is preserved as source data; no role mapping is configured.",
            entity_type="professional",
        )

    return CanonicalProfessional(
        **canonical_envelope(
            context,
            "professional",
            source_id,
            {key: row.get(key) for key in PROFESSIONAL_COLUMNS},
        ),
        code=source_id,
        given_name=text(row.get("First")),
        family_name=text(row.get("Surname")),
        national_id=text(row.get("NIF")),
        role=ProfessionalRole.OTHER,
        license_number=text(row.get("MembershipNumber")),
        email=text(row.get("Email1Address")),
        phone=text(row.get("Phone1")) or text(row.get("Mobile")),
        tenant_label=context.tenant_label,
    )
