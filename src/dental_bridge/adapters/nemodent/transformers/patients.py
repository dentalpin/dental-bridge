"""Transform Nemodent patient identity and contact fields."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from dental_bridge.adapters.nemodent.extractors._allowlist import PATIENT_COLUMNS
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    as_date,
    canonical_envelope,
    text,
    warn_once,
)
from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.patient import CanonicalPatient


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalPatient | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="patient.missing_source_id",
            message="Nemodent patient row has no GUID and was omitted.",
            entity_type="patient",
        )
        return None

    if row.get("SexCode") is not None:
        warn_once(
            context,
            f"patient.sex_unmapped:{row['SexCode']}",
            severity="info",
            code="patient.sex_unmapped",
            message="Nemodent sex code is preserved as source data; no code mapping is configured.",
            entity_type="patient",
        )

    if any(
        row.get(field) is not None for field in ("GUID_ACCOUNT", "GUID_ACCOUNT_HOLDER", "Holder")
    ):
        warn_once(
            context,
            "patient.payer_link_unmapped",
            severity="info",
            code="patient.payer_link_unmapped",
            message=(
                "Nemodent account-holder references are preserved in source data; "
                "client type mapping is not configured."
            ),
            entity_type="patient",
        )

    if row.get("GUID_REFERRER_PATIENT") is not None:
        warn_once(
            context,
            "patient.external_referrer_unmapped",
            severity="info",
            code="patient.external_referrer_unmapped",
            message=(
                "Nemodent patient referrer is external; its identifier is preserved "
                "in source data without a canonical patient link."
            ),
            entity_type="patient",
        )

    center_uuid = _resolve(context, "center", row.get("GUID_CLINIC"), patient_source_id=source_id)
    professional_uuid = _resolve(
        context, "professional", row.get("ID_PERSONNEL_DOCTOR"), patient_source_id=source_id
    )

    return CanonicalPatient(
        **canonical_envelope(
            context,
            "patient",
            source_id,
            {key: row.get(key) for key in PATIENT_COLUMNS},
        ),
        patient_number=text(row.get("CHN")),
        given_name=text(row.get("First")),
        family_name=text(row.get("SurName")),
        national_id=text(row.get("NIF")),
        date_of_birth=as_date(row.get("BirthDate")),
        sex=Sex.UNKNOWN,
        phone=text(row.get("Phone1")),
        mobile_phone=text(row.get("Mobile")),
        fax=text(row.get("Fax")),
        email=text(row.get("Email1Address")),
        address_street=text(row.get("Address")),
        address_postal_code=text(row.get("Zip_Code")),
        notes=text(row.get("Comments")),
        default_center_uuid=center_uuid,
        default_professional_uuid=professional_uuid,
        tenant_label=context.tenant_label,
    )


def _resolve(
    context: TransformContext,
    entity_type: str,
    source_id: object | None,
    *,
    patient_source_id: str,
) -> UUID | None:
    reference_id = text(source_id)
    if reference_id is None:
        return None
    resolved = context.id_mapping.resolve(
        context.source_system,
        entity_type,
        reference_id,
        require_known=True,
    )
    if resolved is None:
        context.warnings.add(
            severity="warn",
            code=f"patient.{entity_type}_unresolved",
            message=f"Nemodent patient references an unexported {entity_type}.",
            entity_type="patient",
            source_id=patient_source_id,
        )
    return resolved
