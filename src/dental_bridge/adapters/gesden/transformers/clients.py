"""Transform a Gesdén ``Clientes`` row into :class:`CanonicalClient`."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.gesden.transformers._context import (
    TransformContext,
    normalise_national_id,
    normalise_string,
    serialise_raw,
    tenant_str,
)
from dental_bridge.core.canonical._enums import ClientKind
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.client import CanonicalClient


def _classify_kind(razon_social: str | None, apellidos: str | None) -> ClientKind:
    """A row with a `RazonSocial` and no person name is a company.

    Several Gesdén installations also create per-patient client rows where
    only the person fields are populated; those are treated as persons.
    """
    if razon_social and not apellidos:
        return ClientKind.COMPANY
    return ClientKind.PERSON


def transform(row: dict[str, Any], ctx: TransformContext) -> CanonicalClient:
    source_id = str(row["IdCli"])

    razon = normalise_string(row.get("RazonSocial"))
    apellidos = normalise_string(row.get("Apellidos"))
    kind = _classify_kind(razon, apellidos)

    parent_uuid = None
    parent_raw = row.get("IdCIA")
    if parent_raw not in (None, "", 0) and str(parent_raw) != source_id:
        parent_uuid = derive_canonical_uuid(ctx.source_system, "client", str(parent_raw))

    return CanonicalClient(
        canonical_uuid=derive_canonical_uuid(ctx.source_system, "client", source_id),
        source_system=ctx.source_system,
        source_id=source_id,
        adapter_version=ctx.adapter_version,
        extracted_at=ctx.now(),
        raw_source_data=serialise_raw(row),
        kind=kind,
        given_name=normalise_string(row.get("Nombre")) if kind is ClientKind.PERSON else None,
        family_name=apellidos if kind is ClientKind.PERSON else None,
        legal_name=razon if kind is ClientKind.COMPANY else None,
        national_id=normalise_national_id(row.get("NIF")),
        email=normalise_string(row.get("Email")),
        default_center_uuid=_resolve_center(row.get("IdCentro"), ctx),
        parent_company_uuid=parent_uuid,
        tenant_label=tenant_str(row.get("Guid_Tenant")),
    )


def _resolve_center(source_id: object | None, ctx: TransformContext):
    if source_id in (None, "", 0, -1):
        return None
    return ctx.id_mapping.resolve(ctx.source_system, "center", source_id)
