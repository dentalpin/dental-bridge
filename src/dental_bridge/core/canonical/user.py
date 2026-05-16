"""CanonicalUser — a login account in the source PMS."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalUser(BaseCanonicalEntity):
    """A staff account that can log in to the source PMS.

    Passwords are **never** migrated. The destination is expected to
    create equivalent accounts and force a password reset via email.
    The link to a ``CanonicalProfessional`` (when the user is also a
    practitioner) is carried via ``professional_uuid``.
    """

    entity_type: str = Field(default="user", frozen=True)

    login: str | None = Field(
        default=None,
        description="Login identifier from the source PMS. May or may not be an email.",
    )
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None

    professional_uuid: UUID | None = Field(
        default=None,
        description="Link to a CanonicalProfessional when the user is also a practitioner.",
    )

    deactivated: bool = False

    tenant_label: str | None = None
