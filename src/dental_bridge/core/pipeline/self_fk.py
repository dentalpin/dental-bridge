"""Reference-validation pass.

Some canonical entities reference rows by canonical UUID — either to
another row of the same type (self-FK: a patient referred by another
patient) or to a row in a different table (an appointment pointing at
its recurrence parent). Because the canonical UUID is derived
deterministically from the source identifier, the value is always
emitted by the transformer regardless of whether the referenced row was
actually included in the current extraction scope.

After all entities have been written, this module sweeps every
registered reference, identifies orphans, NULLs them in the file's
payload via ``json_set`` and records a warning per orphan.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

from dental_bridge.core.pipeline.errors import WarningRegistry


@dataclass(slots=True, frozen=True)
class ReferenceCheck:
    """One UUID-valued payload column to validate after extraction."""

    entity_type: str
    payload_field: str
    referenced_entity_type: str | None = None
    """The entity_type the field points at. ``None`` means same as
    ``entity_type`` (i.e. a classic self-FK)."""

    @property
    def target(self) -> str:
        return self.referenced_entity_type or self.entity_type


# Sprint 2-3-4 set. Append as new entities with cross- or self-references
# are added.
DEFAULT_SELF_FKS: tuple[ReferenceCheck, ...] = (
    ReferenceCheck(entity_type="patient", payload_field="referrer_patient_uuid"),
    ReferenceCheck(entity_type="client", payload_field="parent_company_uuid"),
    ReferenceCheck(
        entity_type="appointment",
        payload_field="recurrence_uuid",
        referenced_entity_type="appointment_recurrence",
    ),
    ReferenceCheck(entity_type="budget", payload_field="alternative_of_uuid"),
    ReferenceCheck(entity_type="budget", payload_field="original_budget_uuid"),
    ReferenceCheck(
        entity_type="budget_line",
        payload_field="applied_treatment_uuid",
        referenced_entity_type="applied_treatment",
    ),
    ReferenceCheck(
        entity_type="applied_treatment",
        payload_field="budget_line_uuid",
        referenced_entity_type="budget_line",
    ),
    # Sprint 5 — financial chain self-FKs and back-references
    ReferenceCheck(entity_type="payment", payload_field="cancelled_by_uuid"),
    ReferenceCheck(entity_type="payment", payload_field="related_payment_uuid"),
    ReferenceCheck(entity_type="debt", payload_field="cancelled_by_uuid"),
    ReferenceCheck(entity_type="fiscal_document", payload_field="origin_document_uuid"),
    # Sprint 6 — clinical secondary
    ReferenceCheck(entity_type="recall", payload_field="origin_recall_uuid"),
)


def validate_and_nullify_orphans(
    conn: sqlite3.Connection,
    warnings: WarningRegistry,
    checks: tuple[ReferenceCheck, ...] = DEFAULT_SELF_FKS,
) -> int:
    """Return the number of orphan references cleaned across all checks."""
    total = 0
    existing_tables = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    for check in checks:
        if check.entity_type not in existing_tables:
            continue
        if check.target not in existing_tables:
            # The referenced table is not in scope at all — every value of
            # this column is necessarily orphan. We still NULL them out so
            # the destination does not have to chase ghosts.
            total += _validate_one(conn, warnings, check, known_uuids=set())
            continue
        known_uuids = {
            row[0] for row in conn.execute(f'SELECT canonical_uuid FROM "{check.target}"')
        }
        total += _validate_one(conn, warnings, check, known_uuids=known_uuids)
    return total


def _validate_one(
    conn: sqlite3.Connection,
    warnings: WarningRegistry,
    check: ReferenceCheck,
    *,
    known_uuids: set[str],
) -> int:
    table = check.entity_type
    cleaned = 0
    cursor = conn.execute(f'SELECT canonical_uuid, source_id, payload FROM "{table}"')
    for canonical_uuid, source_id, payload_json in cursor:
        payload = json.loads(payload_json)
        ref = payload.get(check.payload_field)
        if ref is None or ref in known_uuids:
            continue
        # Orphan reference — null it out and warn.
        conn.execute(
            f'UPDATE "{table}" SET payload = json_set(payload, ?, NULL) WHERE canonical_uuid = ?',
            (f"$.{check.payload_field}", canonical_uuid),
        )
        warnings.add(
            severity="warn",
            code=f"{check.entity_type}.{check.payload_field}.orphan",
            message=(
                f"{check.entity_type}.{check.payload_field} pointed at {ref!r}, "
                f"which is not present in the extraction scope (table "
                f"{check.target!r}); reference NULLed."
            ),
            entity_type=check.entity_type,
            source_id=source_id,
            raw_data={
                "orphan_uuid": ref,
                "field": check.payload_field,
                "target_entity": check.target,
            },
        )
        cleaned += 1
    conn.commit()
    return cleaned


# Backwards-compatible alias kept so callers from Sprint 2 still resolve
# the original name without changes.
SelfFK = ReferenceCheck
