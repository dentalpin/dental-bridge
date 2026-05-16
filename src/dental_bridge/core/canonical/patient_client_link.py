"""CanonicalPatientClientLink — many-to-many relationship between patients and clients."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from dental_bridge.core.canonical.base import BaseCanonicalEntity


class CanonicalPatientClientLink(BaseCanonicalEntity):
    """Records that a given Client is responsible for a given Patient.

    A patient may have several clients (one paying for routine visits,
    another for an insurance policy, a parent for a child). The link carries
    optional policy details and validity dates.
    """

    entity_type: str = Field(default="patient_client_link", frozen=True)

    patient_uuid: UUID
    client_uuid: UUID

    policy_number: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None

    deactivated_at: date | None = None
