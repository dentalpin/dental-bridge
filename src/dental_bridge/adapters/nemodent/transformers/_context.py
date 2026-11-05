"""Shared state and source-value normalization for Nemodent transformers."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from dental_bridge.adapters.nemodent import ADAPTER_NAME, ADAPTER_VERSION
from dental_bridge.core.pipeline.errors import Severity, WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping


@dataclass(slots=True)
class TransformContext:
    source_system: str
    adapter_version: str
    id_mapping: IdMapping
    warnings: WarningRegistry
    tenant_label: str | None = None
    appointment_status_labels: dict[str, str] = field(default_factory=dict)
    appointment_type_labels: dict[str, str] = field(default_factory=dict)
    appointment_type_durations: dict[str, int] = field(default_factory=dict)
    chair_source_ids: set[str] = field(default_factory=set)
    center_source_ids: list[str] = field(default_factory=list)
    location_type_names: dict[str, str] = field(default_factory=dict)
    budget_patient_source_ids: dict[str, str] = field(default_factory=dict)
    reported_warning_keys: set[str] = field(default_factory=set)


def canonical_envelope(
    context: TransformContext,
    entity_type: str,
    source_id: object,
    raw: dict[str, Any],
) -> dict[str, Any]:
    from dental_bridge.core.canonical.base import derive_canonical_uuid

    stable_id = str(source_id)
    return {
        "canonical_uuid": derive_canonical_uuid(ADAPTER_NAME, entity_type, stable_id),
        "source_system": context.source_system,
        "source_id": stable_id,
        "adapter_version": context.adapter_version or ADAPTER_VERSION,
        "extracted_at": datetime.now(UTC),
        "raw_source_data": serialise_raw(raw),
    }


def serialise_raw(row: dict[str, Any]) -> dict[str, Any]:
    """Convert Access values to JSON-compatible values without dropping fields."""
    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, datetime | date | time):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal | UUID):
            result[key] = str(value)
        elif isinstance(value, bytes):
            result[key] = base64.b64encode(value).decode("ascii")
        else:
            result[key] = value
    return result


def text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def warn_once(
    context: TransformContext,
    key: str,
    *,
    severity: Severity,
    code: str,
    message: str,
    entity_type: str,
) -> None:
    if key in context.reported_warning_keys:
        return
    context.reported_warning_keys.add(key)
    context.warnings.add(
        severity=severity,
        code=code,
        message=message,
        entity_type=entity_type,
    )


def as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None
