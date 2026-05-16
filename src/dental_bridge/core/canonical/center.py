"""CanonicalCenter — a clinic, branch or site of operation."""

from __future__ import annotations

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalCenter(BaseCanonicalEntity):
    """A physical clinical site.

    Most Gesdén installations operate a single centre, but multi-clinic
    chains are common. The destination PMS is expected to model each
    centre as a separate site/tenant or branch.
    """

    entity_type: str = Field(default="center", frozen=True)

    code: str | None = Field(
        default=None,
        description="Short identifier the clinic uses internally for this centre.",
    )
    name: str | None = None
    legal_name: str | None = None
    national_id: str | None = Field(
        default=None,
        description="Tax/registration identifier of the legal entity owning the centre.",
    )
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None

    tenant_label: str | None = None
