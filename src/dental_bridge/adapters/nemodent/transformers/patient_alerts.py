"""Transform Nemodent patient alert rows to canonical alerts."""

from __future__ import annotations

from typing import Any

from dental_bridge.adapters.nemodent.extractors._allowlist import PATIENT_ALERT_COLUMNS
from dental_bridge.adapters.nemodent.transformers._context import (
    TransformContext,
    canonical_envelope,
    text,
)
from dental_bridge.core.canonical.clinical_secondary import CanonicalPatientAlert


def transform(row: dict[str, Any], context: TransformContext) -> CanonicalPatientAlert | None:
    source_id = text(row.get("GUID"))
    if source_id is None:
        context.warnings.add(
            severity="error",
            code="patient_alert.missing_source_id",
            message="Nemodent patient alert has no GUID and was omitted.",
            entity_type="patient_alert",
        )
        return None

    patient_uuid = context.id_mapping.resolve(
        context.source_system,
        "patient",
        source_id,
        require_known=True,
    )
    if patient_uuid is None:
        context.warnings.add(
            severity="warn",
            code="patient_alert.patient_unresolved",
            message="Nemodent patient alert references a patient not included in the export.",
            entity_type="patient_alert",
            source_id=source_id,
        )
        return None

    return CanonicalPatientAlert(
        **canonical_envelope(
            context,
            "patient_alert",
            source_id,
            {key: row.get(key) for key in PATIENT_ALERT_COLUMNS},
        ),
        patient_uuid=patient_uuid,
        text=text(row.get("Description")),
        flagged=True,
        tenant_label=context.tenant_label,
    )
