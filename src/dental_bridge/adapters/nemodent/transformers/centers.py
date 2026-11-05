"""Transform Nemodent clinic metadata to the canonical center entity."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import CENTER_COLUMNS
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.center import CanonicalCenter


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalCenter | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="center.missing_source_id",
            message="Nemodent clinic row has no GUID and was omitted.",
            entity_type="center",
        )
        return None

    canonical = CanonicalCenter(
        **canonical_envelope(
            context,
            "center",
            source_id,
            {key: row.get(key) for key in CENTER_COLUMNS},
        ),
        name=text(row.get("Name")),
        national_id=text(row.get("NIF")),
        address=text(row.get("Address")),
        postal_code=text(row.get("Zip_Code")),
        city=text(row.get("City")),
        phone=text(row.get("Phone1")) or text(row.get("Mobile")),
        email=text(row.get("Email1Address")),
        tenant_label=context.tenant_label,
    )
    context.center_source_ids.append(source_id)
    return canonical
