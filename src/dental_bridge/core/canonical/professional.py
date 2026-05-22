"""CanonicalProfessional — a doctor, hygienist or auxiliary."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class ProfessionalRole(StrEnum):
    """Coarse role taxonomy.

    Destination PMSs often distinguish billing/clinical/auxiliary roles
    for permissioning. The source-system's finer-grained role is kept in
    ``raw_source_data`` for adapters that need to be more specific.
    """

    DOCTOR = "doctor"
    HYGIENIST = "hygienist"
    AUXILIARY = "auxiliary"
    ADMIN = "admin"
    OTHER = "other"


class CanonicalProfessional(BaseCanonicalEntity):
    """A person who delivers or supports clinical care.

    ``CanonicalProfessional`` is distinct from ``CanonicalUser``: a
    professional may not have a login account, and a user may not be a
    professional (e.g. an administrative-only login).
    """

    entity_type: str = Field(default="professional", frozen=True)

    code: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    national_id: str | None = None
    role: ProfessionalRole = ProfessionalRole.OTHER

    license_number: str | None = Field(
        default=None,
        description="Numero de colegiado / professional licence identifier.",
    )
    specialty_code: str | None = None
    email: str | None = None
    phone: str | None = None

    deactivated: bool = False

    last_activity_at: date | None = Field(
        default=None,
        description=(
            "Most recent date the source PMS has any clinical trace for this "
            "professional (treatments, budgets, recalls, appointment rows). "
            "Destination importers use it to soft-deactivate staff that have "
            "been inactive for longer than the operator-chosen window."
        ),
    )

    tenant_label: str | None = None
