"""Origin adapter for Nemodent Microsoft Access databases."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date, time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from dental_bridge.adapters.nemodent import ADAPTER_NAME, ADAPTER_VERSION
from dental_bridge.adapters.nemodent.connection import connect
from dental_bridge.adapters.nemodent.extractors._allowlist import (
    APPOINTMENT_DURATION_COLUMNS,
    APPOINTMENT_STATUS_COLUMNS,
    APPOINTMENT_TYPE_COLUMNS,
    BUDGET_COLUMNS,
    BUDGET_LINE_COLUMNS,
    CENTER_COLUMNS,
    CLINIC_LOCATION_COLUMNS,
    CLINIC_LOCATION_TYPE_COLUMNS,
    FISCAL_DOCUMENT_COLUMNS,
    FISCAL_DOCUMENT_LINE_COLUMNS,
    MASTER_PROCEDURE_COLUMNS,
    MASTER_PROCEDURE_TYPE_COLUMNS,
    PATIENT_ALERT_COLUMNS,
    PATIENT_COLUMNS,
    PATIENT_TASK_TRACING_COLUMNS,
    PROCEDURE_COLUMNS,
    PROFESSIONAL_COLUMNS,
)
from dental_bridge.adapters.nemodent.extractors._rows import iter_rows
from dental_bridge.adapters.nemodent.extractors.applied_treatments import (
    iter_joined_rows as iter_applied_treatment_rows,
)
from dental_bridge.adapters.nemodent.extractors.appointments import iter_joined_rows
from dental_bridge.adapters.nemodent.schema_fingerprint import compute_fingerprint
from dental_bridge.adapters.nemodent.transformers import (
    applied_treatment_phases,
    applied_treatments,
    appointments,
    budgets,
    catalog_items,
    centers,
    fiscal_documents,
    patient_alerts,
    patients,
    professionals,
)
from dental_bridge.adapters.nemodent.transformers._context import TransformContext
from dental_bridge.adapters.nemodent.version_registry import (
    KnownFingerprint,
)
from dental_bridge.adapters.nemodent.version_registry import (
    lookup as lookup_fingerprint,
)
from dental_bridge.core.adapters.origin_abc import OriginAdapter
from dental_bridge.core.canonical.appointment import AppointmentStatus, CanonicalAppointment
from dental_bridge.core.canonical.base import BaseCanonicalEntity
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping

if TYPE_CHECKING:
    import pyodbc

_SIMPLE_ENTITY_PIPELINE: dict[
    str,
    tuple[str, tuple[str, ...], Callable[[dict[str, Any], TransformContext], Any]],
] = {
    "center": ("CLINIC", CENTER_COLUMNS, centers.transform),
    "professional": ("PERSONNEL", PROFESSIONAL_COLUMNS, professionals.transform),
    "patient": ("Patient", PATIENT_COLUMNS, patients.transform),
}

_DEFAULT_ORDER = [
    "center",
    "professional",
    "catalog_item",
    "patient",
    "appointment",
    "treatment_catalog_item",
    "treatment_catalog_variant",
    "applied_treatment",
    "applied_treatment_phase",
    "budget",
    "budget_line",
    "patient_alert",
    "fiscal_document",
    "fiscal_document_line",
]

_ACTIVE_APPOINTMENT_STATUSES = {
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.UNKNOWN,
}


class NemodentAdapter(OriginAdapter):
    """Read a local Nemodent MDB and yield canonical entities."""

    name = ADAPTER_NAME
    version = ADAPTER_VERSION

    def __init__(
        self,
        *,
        id_mapping: IdMapping | None = None,
        warnings: WarningRegistry | None = None,
    ) -> None:
        self._conn: pyodbc.Connection | None = None
        self._ctx = TransformContext(
            source_system=self.name,
            adapter_version=self.version,
            id_mapping=id_mapping if id_mapping is not None else IdMapping(),
            warnings=warnings if warnings is not None else WarningRegistry(),
        )

    def connect(self, dsn: str, **kwargs: object) -> None:
        tenant_label = kwargs.get("tenant_label")
        if self._conn is not None:
            self.close()
        self._ctx.tenant_label = (
            tenant_label if isinstance(tenant_label, str) else Path(dsn).stem or None
        )
        self._conn = connect(dsn)

    def fingerprint(self) -> str:
        return compute_fingerprint(self._require_conn())

    def supported_entities(self) -> list[str]:
        return list(_DEFAULT_ORDER)

    def default_entity_order(self) -> list[str]:
        return list(_DEFAULT_ORDER)

    def iter_entity(self, entity_type: str) -> Iterator[BaseCanonicalEntity]:
        if entity_type == "catalog_item":
            yield from self._iter_catalog_items()
            return
        if entity_type == "appointment":
            seen_slots: set[tuple[UUID, UUID, date, time]] = set()
            for row in iter_joined_rows(self._require_conn()):
                appointment = appointments.transform(row, self._ctx)
                if appointment is None:
                    continue
                slot_key = _appointment_target_slot_key(appointment)
                if slot_key is not None and slot_key in seen_slots:
                    self._ctx.warnings.add(
                        severity="warn",
                        code="appointment.duplicate_slot_omitted",
                        message=(
                            "Nemodent appointment duplicates an earlier active "
                            "chair/professional/start-time slot in this export and was omitted."
                        ),
                        entity_type="appointment",
                        source_id=appointment.source_id,
                    )
                    continue
                if slot_key is not None:
                    seen_slots.add(slot_key)
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    appointment.entity_type,
                    appointment.source_id,
                )
                yield appointment
            return
        if entity_type == "applied_treatment":
            for row in iter_applied_treatment_rows(self._require_conn()):
                applied_treatment = applied_treatments.transform(row, self._ctx)
                if applied_treatment is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    applied_treatment.entity_type,
                    applied_treatment.source_id,
                )
                yield applied_treatment
            return
        if entity_type == "applied_treatment_phase":
            for row in iter_rows(
                self._require_conn(),
                table="PATIENT_TASKS_TRACING",
                columns=PATIENT_TASK_TRACING_COLUMNS,
            ):
                phase = applied_treatment_phases.transform(row, self._ctx)
                if phase is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    phase.entity_type,
                    phase.source_id,
                )
                yield phase
            return
        if entity_type == "budget":
            for row in iter_rows(
                self._require_conn(),
                table="ESTIMATES",
                columns=BUDGET_COLUMNS,
            ):
                budget = budgets.transform_budget(row, self._ctx)
                if budget is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    budget.entity_type,
                    budget.source_id,
                )
                yield budget
            return
        if entity_type == "budget_line":
            for row in iter_rows(
                self._require_conn(),
                table="ESTIMATES_PROCEDURES",
                columns=BUDGET_LINE_COLUMNS,
            ):
                line = budgets.transform_budget_line(row, self._ctx)
                if line is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    line.entity_type,
                    line.source_id,
                )
                yield line
            return
        if entity_type == "patient_alert":
            for row in iter_rows(
                self._require_conn(),
                table="PatientAlerts",
                columns=PATIENT_ALERT_COLUMNS,
            ):
                alert = patient_alerts.transform(row, self._ctx)
                if alert is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    alert.entity_type,
                    alert.source_id,
                )
                yield alert
            return
        if entity_type == "fiscal_document":
            for row in iter_rows(
                self._require_conn(),
                table="INVOICE_HEADING",
                columns=FISCAL_DOCUMENT_COLUMNS,
            ):
                document = fiscal_documents.transform_document(row, self._ctx)
                if document is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    document.entity_type,
                    document.source_id,
                )
                yield document
            return
        if entity_type == "fiscal_document_line":
            for row in iter_rows(
                self._require_conn(),
                table="INVOICE_DETAILS",
                columns=FISCAL_DOCUMENT_LINE_COLUMNS,
            ):
                fiscal_line = fiscal_documents.transform_document_line(row, self._ctx)
                if fiscal_line is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    fiscal_line.entity_type,
                    fiscal_line.source_id,
                )
                yield fiscal_line
            return
        if entity_type == "treatment_catalog_item":
            for row in iter_rows(
                self._require_conn(),
                table="MASTER_PROCEDURES",
                columns=MASTER_PROCEDURE_COLUMNS,
            ):
                treatment = catalog_items.transform_treatment(row, self._ctx)
                if treatment is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    treatment.entity_type,
                    treatment.source_id,
                )
                yield treatment
            return
        if entity_type == "treatment_catalog_variant":
            for row in iter_rows(
                self._require_conn(),
                table="PROCEDURES",
                columns=PROCEDURE_COLUMNS,
            ):
                variant = catalog_items.transform_treatment_variant(row, self._ctx)
                if variant is None:
                    continue
                self._ctx.id_mapping.register(
                    self._ctx.source_system,
                    variant.entity_type,
                    variant.source_id,
                )
                yield variant
            return

        pipeline = _SIMPLE_ENTITY_PIPELINE.get(entity_type)
        if pipeline is None:
            raise KeyError(f"Nemodent adapter does not support entity {entity_type!r}")

        source_table, source_columns, transformer = pipeline
        for row in iter_rows(
            self._require_conn(),
            table=source_table,
            columns=source_columns,
        ):
            entity = transformer(row, self._ctx)
            if entity is None:
                continue
            self._ctx.id_mapping.register(
                self._ctx.source_system,
                entity.entity_type,
                entity.source_id,
            )
            yield entity

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def context(self) -> TransformContext:
        return self._ctx

    @staticmethod
    def lookup_fingerprint(fingerprint: str) -> KnownFingerprint | None:
        return lookup_fingerprint(fingerprint)

    def _require_conn(self) -> pyodbc.Connection:
        if self._conn is None:
            raise RuntimeError("NemodentAdapter is not connected — call connect() first")
        return self._conn

    def _iter_catalog_items(self) -> Iterator[BaseCanonicalEntity]:
        conn = self._require_conn()
        for row in iter_rows(
            conn,
            table="MASTER_PROCEDURE_TYPES",
            columns=MASTER_PROCEDURE_TYPE_COLUMNS,
        ):
            canonical = catalog_items.transform_specialty(row, self._ctx)
            if canonical is None:
                continue
            self._ctx.id_mapping.register(
                self._ctx.source_system,
                canonical.entity_type,
                canonical.source_id,
            )
            yield canonical

        durations: dict[str, int] = {}
        for row in iter_rows(
            conn,
            table="APPOINTMENT_DURATIONS",
            columns=APPOINTMENT_DURATION_COLUMNS,
        ):
            guid = str(row["GUID"]).strip() if row["GUID"] is not None else ""
            try:
                minutes = int(row["Hour"]) * 60 + int(row["Min"])
            except (TypeError, ValueError):
                minutes = 0
            if guid and minutes > 0:
                durations[guid] = minutes

        for row in iter_rows(
            conn,
            table="APPOINTMENT_TYPES",
            columns=APPOINTMENT_TYPE_COLUMNS,
        ):
            type_id = str(row["GUID"]).strip() if row["GUID"] is not None else ""
            if not type_id:
                continue
            name = str(row["Name"]).strip() if row["Name"] is not None else ""
            if name:
                self._ctx.appointment_type_labels[type_id] = name
            duration_id = (
                str(row["GUID_DURATION"]).strip() if row["GUID_DURATION"] is not None else ""
            )
            if duration_id in durations:
                self._ctx.appointment_type_durations[type_id] = durations[duration_id]

        for row in iter_rows(
            conn,
            table="CLINIC_LOCATION_TYPES",
            columns=CLINIC_LOCATION_TYPE_COLUMNS,
        ):
            type_id = str(row["ID"]).strip() if row["ID"] is not None else ""
            type_name = str(row["Name"]).strip() if row["Name"] is not None else ""
            if type_id and type_name:
                self._ctx.location_type_names[type_id] = type_name

        for row in iter_rows(
            conn,
            table="CLINIC_LOCATIONS",
            columns=CLINIC_LOCATION_COLUMNS,
        ):
            canonical = catalog_items.transform_location(row, self._ctx)
            if canonical is None:
                continue
            self._ctx.id_mapping.register(
                self._ctx.source_system,
                canonical.entity_type,
                canonical.source_id,
            )
            yield canonical

        for row in iter_rows(
            conn,
            table="APPOINTMENT_STATUS",
            columns=APPOINTMENT_STATUS_COLUMNS,
        ):
            canonical = catalog_items.transform_appointment_status(row, self._ctx)
            if canonical is None:
                continue
            self._ctx.id_mapping.register(
                self._ctx.source_system,
                canonical.entity_type,
                canonical.source_id,
            )
            yield canonical


def _appointment_target_slot_key(
    appointment: CanonicalAppointment,
) -> tuple[UUID, UUID, date, time] | None:
    """Return DentalPin's active-slot key when the source row can occupy one."""
    if appointment.coarse_status not in _ACTIVE_APPOINTMENT_STATUSES:
        return None
    if (
        appointment.chair_uuid is None
        or appointment.professional_uuid is None
        or appointment.scheduled_date is None
        or appointment.scheduled_time is None
    ):
        return None
    return (
        appointment.chair_uuid,
        appointment.professional_uuid,
        appointment.scheduled_date,
        appointment.scheduled_time,
    )
