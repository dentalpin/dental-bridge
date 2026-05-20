"""Canonical entities for treatments applied to a patient.

``AppliedTreatment`` represents one ``TtosMed`` row — the clinical event
of executing a treatment template on a specific patient. Its phases live
in ``AppliedTreatmentPhase``.

The odontogram (which tooth, which surface, which condition) is encoded
in Gesdén across the ``ZonasBoca``, ``PiezasAdu``, ``PiezasLec``,
``PiezasNum``, ``ZonasPieza``, ``IdTipoOdg``, ``DespX``, ``DespY``,
``Rotacion``, ``Cuadrantes`` and ``Arcadas`` columns. These are
preserved verbatim in ``raw_source_data`` and surfaced as opaque
integers in ``odontogram_raw`` so importers that know how to decode
them can do so; decoding the bit-mask is deferred to a later sprint
once empirical validation against the Gesdén UI is in place.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalAppliedTreatment(BaseCanonicalEntity):
    """A treatment executed (or scheduled to be executed) on a patient."""

    entity_type: str = Field(default="applied_treatment", frozen=True)

    # References ----------------------------------------------------------
    patient_uuid: UUID | None = None
    client_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    auxiliary_professional_uuid: UUID | None = None
    center_uuid: UUID | None = None
    treatment_variant_uuid: UUID | None = Field(
        default=None,
        description="Reference to the Tratamientos_Tarifas row this was instantiated from.",
    )
    user_uuid: UUID | None = None
    budget_line_uuid: UUID | None = Field(
        default=None,
        description=(
            "When this treatment was created from a budget line, the canonical "
            "UUID of that BudgetLine. Forms the back-half of the Presu↔TtosMed "
            "double link."
        ),
    )
    referral_source_uuid: UUID | None = None

    # Numbering -----------------------------------------------------------
    treatment_number: str | None = None

    # Lifecycle ----------------------------------------------------------
    status_code: int | None = Field(
        default=None,
        description=(
            "Source ``StaTto`` value. The destination interprets it; "
            "dominant value 5 = realized/billable per docs/schema_map.md."
        ),
    )
    start_date: date | None = None
    end_date: date | None = None
    expiry_date: date | None = None
    validated_at: datetime | None = None

    # Money ---------------------------------------------------------------
    amount: Decimal | None = None
    discount_percent: Decimal | None = None
    discount_amount: Decimal | None = None
    pending_amount: Decimal | None = None
    private_amount: Decimal | None = None
    mutua_amount: Decimal | None = None

    # Volume / sessions --------------------------------------------------
    units: int | None = None
    sessions_performed: int | None = None

    notes: str | None = None

    # Odontogram raw (not decoded yet). All values are opaque ints.
    odontogram_raw: dict[str, int | None] = Field(
        default_factory=dict,
        description=(
            "Verbatim copies of the source columns that encode the tooth/surface "
            "selection: zonas_pieza, piezas_adu, piezas_lec, piezas_num, "
            "id_tipo_odg, cuadrantes, arcadas, desp_x, desp_y, rotacion. "
            "Decoding for surfaces (zonas_pieza) is deferred pending UI validation."
        ),
    )
    teeth: list[int] = Field(
        default_factory=list,
        description=(
            "FDI numbers decoded from PiezasAdu (adult) + PiezasLec (deciduous). "
            "Empty when the source row carries no tooth selection or the value is "
            "0. Best-effort mapping reverse-engineered from frequency analysis — "
            "see ``adapters/gesden/decoders/odontogram.py``."
        ),
    )

    # Legal / fiscal references (immutable history) -----------------------
    document_number: str | None = Field(
        default=None,
        description="NumDocUnico — the legal document number assigned at billing time.",
    )
    transaction_number: str | None = None

    tenant_label: str | None = None


class CanonicalAppliedTreatmentPhase(BaseCanonicalEntity):
    """One phase of an ``AppliedTreatment``."""

    entity_type: str = Field(default="applied_treatment_phase", frozen=True)

    applied_treatment_uuid: UUID
    phase_template_uuid: UUID | None = None
    professional_uuid: UUID | None = None
    auxiliary_professional_uuid: UUID | None = None

    phase_number: int | None = None
    status_code: int | None = None
    executed_on: date | None = None
    percent_to_bill: Decimal | None = None
    notes: str | None = None

    tenant_label: str | None = None
