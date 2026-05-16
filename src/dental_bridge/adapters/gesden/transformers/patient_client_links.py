"""Transform a Gesdén ``PacCli`` row into :class:`CanonicalPatientClientLink`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.decoders.sentinel_dates import clean_date
from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_string,
    serialise_raw,
)
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.patient_client_link import CanonicalPatientClientLink


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalPatientClientLink:
    pac = str(row["IdPac"])
    cli = str(row["IdCli"])
    composite_source_id = f"{pac}:{cli}"

    return CanonicalPatientClientLink(
        canonical_uuid=derive_canonical_uuid(
            ctx.source_system, "patient_client_link", composite_source_id
        ),
        source_system=ctx.source_system,
        source_id=composite_source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        patient_uuid=derive_canonical_uuid(ctx.source_system, "patient", pac),
        client_uuid=derive_canonical_uuid(ctx.source_system, "client", cli),
        policy_number=normalise_string(row.get("Poliza")),
        valid_from=clean_date(row.get("FecAlta")),
        valid_until=clean_date(row.get("FecCaduc")),
        deactivated_at=clean_date(row.get("Inactivo")),
    )
