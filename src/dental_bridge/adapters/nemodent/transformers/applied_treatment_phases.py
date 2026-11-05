"""Transform Nemodent task tracing rows into canonical treatment phases."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import (
    PATIENT_TASK_TRACING_COLUMNS,
)
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    as_date,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.applied_treatment import CanonicalAppliedTreatmentPhase


def transform(
    row: dict[str, Any], context: TransformContext
) -> CanonicalAppliedTreatmentPhase | None:
    task_id = text(row.get("GUID_TASK"))
    session_date = as_date(row.get("Date"))
    start_time = _as_time(row.get("StartTime"))
    if task_id is None or session_date is None or start_time is None:
        context.warnings.add(
            severity="error",
            code="applied_treatment_phase.missing_source_key",
            message="Nemodent treatment tracing row is missing a primary-key field and was omitted.",
            entity_type="applied_treatment_phase",
        )
        return None

    source_id = f"{task_id}:{session_date.isoformat()}:{start_time.isoformat()}"
    applied_treatment_uuid = context.id_mapping.resolve(
        context.source_system,
        "applied_treatment",
        task_id,
        require_known=True,
    )
    if applied_treatment_uuid is None:
        context.warnings.add(
            severity="warn",
            code="applied_treatment_phase.parent_unresolved",
            message="Nemodent treatment tracing row has no exported parent treatment and was omitted.",
            entity_type="applied_treatment_phase",
            source_id=source_id,
        )
        return None

    return CanonicalAppliedTreatmentPhase(
        **canonical_envelope(
            context,
            "applied_treatment_phase",
            source_id,
            {key: row.get(key) for key in PATIENT_TASK_TRACING_COLUMNS},
        ),
        applied_treatment_uuid=applied_treatment_uuid,
        status_code=_optional_int(row.get("Status")),
        executed_on=session_date,
        tenant_label=context.tenant_label,
    )


def _as_time(value: Any) -> time | None:
    if isinstance(value, datetime):
        return value.time().replace(tzinfo=None)
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    return None


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
