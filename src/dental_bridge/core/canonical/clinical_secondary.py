"""Canonical entities for secondary clinical data.

This module groups the entities that depend on Patient but live outside
the core treatment/budget/financial axis: pharmacological history,
prescriptions, consents, attached documents, recalls and patient alerts.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalPharmacologicalHistory(BaseCanonicalEntity):
    """Patient's medication / pharmacological-history record (``TTratamientos``)."""

    entity_type: str = Field(default="pharmacological_history", frozen=True)

    patient_uuid: UUID
    professional_uuid: UUID | None = None
    center_uuid: UUID | None = None
    drug_uuid: UUID | None = Field(
        default=None,
        description="canonical_uuid of the TAuxFarmacos catalog row, when set.",
    )

    drug_description: str | None = None
    dose: str | None = None
    dosage: str | None = None
    administration_route: str | None = None
    frequency: str | None = None
    observations: str | None = None
    record_kind: int | None = None
    public: bool | None = None

    start_date: date | None = None
    end_date: date | None = None

    tenant_label: str | None = None


class CanonicalPrescription(BaseCanonicalEntity):
    """A prescription (``RecetasCab``)."""

    entity_type: str = Field(default="prescription", frozen=True)

    patient_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    center_uuid: UUID | None = None

    issued_on: date | None = None
    inserted_on: datetime | None = None
    printed_on: datetime | None = None

    description: str | None = None
    notes: str | None = None
    pharmacist_notes: str | None = None
    diagnosis: str | None = None
    prescription_kind: int | None = None
    cve: str | None = None

    dispensed: bool = False
    print_count: int | None = None
    cancelled: bool = False
    public: bool | None = None

    tenant_label: str | None = None


class CanonicalPrescriptionItem(BaseCanonicalEntity):
    """One prescribed drug within a :class:`CanonicalPrescription`."""

    entity_type: str = Field(default="prescription_item", frozen=True)

    prescription_uuid: UUID
    patient_uuid: UUID | None = None
    drug_uuid: UUID | None = None

    drug_description: str | None = None
    pattern: str | None = None
    posology: str | None = None
    units: int | None = None
    packages: int | None = None
    duration: str | None = None
    dispense_order: int | None = None
    previous_dispensation: str | None = None

    tenant_label: str | None = None


class CanonicalConsent(BaseCanonicalEntity):
    """A signed consent document (``TConsinCab``).

    Only the rendered ``Texto`` / ``Html`` is migrated. The key-value
    detail rows (``TConsinDet``) are not exported — they depend on
    template files that live outside the database and are not
    reconstructable on their own.
    """

    entity_type: str = Field(default="consent", frozen=True)

    patient_uuid: UUID
    professional_uuid: UUID | None = None
    signed_by_user_uuid: UUID | None = None
    signed_by_professional_uuid: UUID | None = None

    title: str | None = None
    representative: str | None = None
    doctor_name: str | None = None
    college_number: str | None = None
    rendered_text: str | None = Field(
        default=None,
        description="Verbatim copy of the signed text (``Texto`` column).",
    )
    rendered_html: str | None = Field(
        default=None,
        description="Verbatim copy of the signed HTML (``Html`` column).",
    )

    generated_on: datetime | None = None
    signed_on: datetime | None = None
    print_count: int | None = None
    signed: bool = False

    tenant_label: str | None = None


class CanonicalPatientDocument(BaseCanonicalEntity):
    """A document attached to a patient (``TDocumentosPac``).

    The binary content is **not** included in the DPMF file. The Document
    entity carries the metadata and a single companion row is appended to
    the ``_files`` manifest so a sync agent can transfer the binary
    out-of-band.
    """

    entity_type: str = Field(default="patient_document", frozen=True)

    patient_uuid: UUID
    user_uuid: UUID | None = None
    signed_by_user_uuid: UUID | None = None

    document_date: date | None = None
    inserted_on: datetime | None = None
    description: str | None = None
    notes: str | None = None
    original_filename: str | None = Field(
        default=None,
        description="Original filename from TDocumentosPac.Original, no path.",
    )
    document_kind: int | None = None
    signed: bool = False

    tenant_label: str | None = None


class CanonicalRecall(BaseCanonicalEntity):
    """A scheduled patient recall (``Recalls``)."""

    entity_type: str = Field(default="recall", frozen=True)

    patient_uuid: UUID
    professional_uuid: UUID | None = None
    reviewer_professional_uuid: UUID | None = None
    center_uuid: UUID | None = None

    reason_uuid: UUID | None = None
    result_uuid: UUID | None = None
    related_budget_uuid: UUID | None = None
    related_applied_treatment_uuid: UUID | None = None
    origin_recall_uuid: UUID | None = Field(
        default=None,
        description="Self-FK: the original recall this one descends from (IdRecallOrigen).",
    )

    recall_number: int | None = None
    scheduled_date: date | None = None
    contact_date: date | None = None

    contact_method_telephone: bool = False
    contact_method_letter: bool = False
    contact_method_email: bool = False
    contact_method_sms: bool = False

    attended: bool = False
    scheduled: bool = False
    status_code: int | None = None

    comments: str | None = None
    observations: str | None = None

    tenant_label: str | None = None


class CanonicalPatientAlert(BaseCanonicalEntity):
    """A flag/note shown when opening a patient record (``AlertPac``)."""

    entity_type: str = Field(default="patient_alert", frozen=True)

    patient_uuid: UUID
    center_uuid: UUID | None = None

    alert_number: int | None = None
    text: str | None = None
    flagged: bool = False

    tenant_label: str | None = None


class CanonicalCommunication(BaseCanonicalEntity):
    """An outbound or inbound communication header (``EdMail`` / patient message).

    Captures the run-level header. Per-recipient detail rows (``EdMailL``)
    are deliberately not exported in v0.1 — they have no stable PK and
    their value is reconstructible from the headers plus the patient
    list filter.
    """

    entity_type: str = Field(default="communication", frozen=True)

    user_uuid: UUID | None = None
    center_uuid: UUID | None = None
    kind: str = Field(
        default="email",
        description=(
            "Loosely the source-system family. 'email' for EdMail runs, "
            "'patient_message' for PacMensajes rows."
        ),
    )

    sent_from: datetime | None = None
    sent_to: datetime | None = None
    document_reference: str | None = None
    notes: str | None = None
    filter_description: str | None = None

    tenant_label: str | None = None
