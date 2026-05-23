"""CanonicalClient — the payer or contracting party."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical._enums import ClientKind
from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalClient(BaseCanonicalEntity):
    """The party that pays for a patient's care.

    A Client may be the patient themselves, a family member, an insurance
    company, a school, or any other legal entity that holds responsibility
    for fees. The link from patient to client is many-to-many and lives in
    `PatientClientLink`.
    """

    entity_type: str = Field(default="client", frozen=True)

    kind: ClientKind = Field(
        default=ClientKind.PERSON,
        description="Whether this client is a natural person or a legal entity.",
    )

    # Person fields ---------------------------------------------------------
    given_name: str | None = None
    family_name: str | None = None

    # Company fields --------------------------------------------------------
    legal_name: str | None = Field(
        default=None,
        description="Razón social for legal entities. Null for natural persons.",
    )

    # Common ----------------------------------------------------------------
    national_id: str | None = None
    email: str | None = None
    phone: str | None = Field(
        default=None,
        description="Primary landline (Gesdén ``Clientes.Tel1``).",
    )
    phone_secondary: str | None = Field(
        default=None,
        description="Secondary landline (Gesdén ``Clientes.Tel2``).",
    )
    mobile_phone: str | None = Field(
        default=None,
        description="Mobile phone (Gesdén ``Clientes.TelMovil``).",
    )
    fax: str | None = None
    address_street: str | None = Field(
        default=None,
        description="Free-text street + number (Gesdén ``Clientes.Direccion``).",
    )
    address_postal_code: str | None = Field(
        default=None,
        description="Postal code (Gesdén ``Clientes.CP``).",
    )

    # References ------------------------------------------------------------
    default_center_uuid: UUID | None = None
    parent_company_uuid: UUID | None = Field(
        default=None,
        description=(
            "Self-FK for client hierarchies (e.g. branch of an insurance "
            "company). Resolved in a second pass."
        ),
    )

    tenant_label: str | None = None
