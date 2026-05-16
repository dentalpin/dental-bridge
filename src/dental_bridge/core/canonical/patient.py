"""CanonicalPatient — the clinical subject."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalPatient(BaseCanonicalEntity):
    """A person who receives clinical care.

    Foreign references are stored as canonical UUIDs of the related entity,
    resolved via the pipeline's ID-mapping registry. When a reference cannot
    be resolved at extract time (e.g. self-FK to a patient not yet emitted),
    the field is left ``None`` and the source identifier remains available
    under ``raw_source_data`` for a later resolution pass.
    """

    entity_type: str = Field(default="patient", frozen=True)

    # Identity --------------------------------------------------------------
    patient_number: str | None = Field(
        default=None,
        description="Human-readable patient number assigned by the clinic.",
    )
    given_name: str | None = None
    family_name: str | None = None
    national_id: str | None = Field(
        default=None,
        description="Government-issued identifier (NIF/NIE in Spain). May be empty.",
    )
    date_of_birth: date | None = None
    sex: Sex = Sex.UNKNOWN

    # Lifecycle -------------------------------------------------------------
    registered_at: date | None = Field(
        default=None,
        description="Date the patient was first recorded in the source PMS.",
    )
    deactivated_at: date | None = Field(
        default=None,
        description="Set when the source PMS marks the patient as inactive.",
    )
    deceased: bool = Field(
        default=False,
        description="True when the source PMS marks the patient as deceased.",
    )
    deceased_at: date | None = None

    # Consent / privacy -----------------------------------------------------
    gdpr_consent: bool | None = Field(
        default=None,
        description="Whether the source PMS records explicit GDPR consent.",
    )

    # Foreign references (resolved via id_mapping) --------------------------
    default_center_uuid: UUID | None = None
    default_professional_uuid: UUID | None = None
    guardian_client_uuid: UUID | None = Field(
        default=None,
        description="Legal guardian, recorded as a Client in the source PMS.",
    )
    referrer_patient_uuid: UUID | None = Field(
        default=None,
        description=(
            "Patient who referred this one. Self-FK — may be resolved in a "
            "second pass after all patients have been emitted."
        ),
    )

    # Multi-tenant guard ----------------------------------------------------
    tenant_label: str | None = Field(
        default=None,
        description=(
            "Source-system tenant identifier. The extractor refuses to mix "
            "tenants in a single DPMF file."
        ),
    )
