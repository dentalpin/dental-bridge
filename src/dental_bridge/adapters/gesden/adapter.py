"""Aggregator class wiring Gesdén extractors, transformers and connection."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden import ADAPTER_NAME, ADAPTER_VERSION
from dental_bridge.adapters.gesden.connection import connect
from dental_bridge.adapters.gesden.extractors import (
    applied_treatment_phases as applied_treatment_phases_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    applied_treatments as applied_treatments_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    appointment_recurrences as appt_rec_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    appointments as appointments_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    budget_lines as budget_lines_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    budgets as budgets_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    catalogs as catalogs_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    centers as centers_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    clients as clients_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    communications as communications_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    consents as consents_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    debt_payment_applications as dpa_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    debts as debts_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    fiscal_document_lines as fiscal_document_lines_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    fiscal_documents as fiscal_documents_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    patient_alerts as patient_alerts_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    patient_client_links as pcl_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    patient_documents as patient_documents_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    patients as patients_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    payments as payments_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    pharmacological_history as pharmacological_history_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    prescription_items as prescription_items_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    prescriptions as prescriptions_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    professionals as professionals_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    recalls as recalls_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    treatment_catalog_items as treatment_catalog_items_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    treatment_catalog_variants as treatment_catalog_variants_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    treatment_phase_templates as treatment_phase_templates_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    users as users_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    work_calendar_days as work_calendar_days_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    work_calendar_shifts as work_calendar_shifts_extractor,
)
from dental_bridge.adapters.gesden.extractors import (
    work_calendars as work_calendars_extractor,
)
from dental_bridge.adapters.gesden.schema_fingerprint import compute_fingerprint
from dental_bridge.adapters.gesden.transformers import (
    applied_treatment_phases as applied_treatment_phases_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    applied_treatments as applied_treatments_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    appointment_recurrences as appt_rec_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    appointments as appointments_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    budget_lines as budget_lines_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    budgets as budgets_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    catalogs as catalogs_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    centers as centers_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    clients as clients_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    communications as communications_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    consents as consents_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    debt_payment_applications as dpa_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    debts as debts_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    fiscal_document_lines as fiscal_document_lines_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    fiscal_documents as fiscal_documents_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    patient_alerts as patient_alerts_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    patient_client_links as pcl_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    patient_documents as patient_documents_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    patients as patients_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    payments as payments_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    pharmacological_history as pharmacological_history_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    prescription_items as prescription_items_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    prescriptions as prescriptions_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    professionals as professionals_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    recalls as recalls_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    treatment_catalog_items as treatment_catalog_items_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    treatment_catalog_variants as treatment_catalog_variants_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    treatment_phase_templates as treatment_phase_templates_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    users as users_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    work_calendar_days as work_calendar_days_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    work_calendar_shifts as work_calendar_shifts_transformer,
)
from dental_bridge.adapters.gesden.transformers import (
    work_calendars as work_calendars_transformer,
)
from dental_bridge.adapters.gesden.transformers._context import TransformContext
from dental_bridge.core.adapters.origin_abc import OriginAdapter
from dental_bridge.core.canonical.base import BaseCanonicalEntity
from dental_bridge.core.pipeline.errors import WarningRegistry
from dental_bridge.core.pipeline.id_mapping import IdMapping

if TYPE_CHECKING:
    import pyodbc

_SIMPLE_ENTITY_PIPELINE: dict[
    str,
    tuple[
        Callable[[pyodbc.Connection], Iterator[dict[str, Any]]],
        Callable[[dict[str, Any], TransformContext], BaseCanonicalEntity],
    ],
] = {
    "center": (centers_extractor.iter_rows, centers_transformer.transform),
    "professional": (
        professionals_extractor.iter_rows,
        professionals_transformer.transform,
    ),
    "user": (users_extractor.iter_rows, users_transformer.transform),
    "work_calendar": (
        work_calendars_extractor.iter_rows,
        work_calendars_transformer.transform,
    ),
    "work_calendar_day": (
        work_calendar_days_extractor.iter_rows,
        work_calendar_days_transformer.transform,
    ),
    "work_calendar_shift": (
        work_calendar_shifts_extractor.iter_rows,
        work_calendar_shifts_transformer.transform,
    ),
    "patient": (patients_extractor.iter_rows, patients_transformer.transform),
    "client": (clients_extractor.iter_rows, clients_transformer.transform),
    "patient_client_link": (pcl_extractor.iter_rows, pcl_transformer.transform),
    "appointment_recurrence": (
        appt_rec_extractor.iter_rows,
        appt_rec_transformer.transform,
    ),
    "appointment": (
        appointments_extractor.iter_rows,
        appointments_transformer.transform,
    ),
    "treatment_catalog_item": (
        treatment_catalog_items_extractor.iter_rows,
        treatment_catalog_items_transformer.transform,
    ),
    "treatment_catalog_variant": (
        treatment_catalog_variants_extractor.iter_rows,
        treatment_catalog_variants_transformer.transform,
    ),
    "treatment_phase_template": (
        treatment_phase_templates_extractor.iter_rows,
        treatment_phase_templates_transformer.transform,
    ),
    "budget": (budgets_extractor.iter_rows, budgets_transformer.transform),
    "budget_line": (budget_lines_extractor.iter_rows, budget_lines_transformer.transform),
    "applied_treatment": (
        applied_treatments_extractor.iter_rows,
        applied_treatments_transformer.transform,
    ),
    "applied_treatment_phase": (
        applied_treatment_phases_extractor.iter_rows,
        applied_treatment_phases_transformer.transform,
    ),
    "debt": (debts_extractor.iter_rows, debts_transformer.transform),
    "payment": (payments_extractor.iter_rows, payments_transformer.transform),
    "debt_payment_application": (
        dpa_extractor.iter_rows,
        dpa_transformer.transform,
    ),
    "fiscal_document": (
        fiscal_documents_extractor.iter_rows,
        fiscal_documents_transformer.transform,
    ),
    "fiscal_document_line": (
        fiscal_document_lines_extractor.iter_rows,
        fiscal_document_lines_transformer.transform,
    ),
    "pharmacological_history": (
        pharmacological_history_extractor.iter_rows,
        pharmacological_history_transformer.transform,
    ),
    "prescription": (
        prescriptions_extractor.iter_rows,
        prescriptions_transformer.transform,
    ),
    "prescription_item": (
        prescription_items_extractor.iter_rows,
        prescription_items_transformer.transform,
    ),
    "consent": (consents_extractor.iter_rows, consents_transformer.transform),
    "patient_document": (
        patient_documents_extractor.iter_rows,
        patient_documents_transformer.transform,
    ),
    "recall": (recalls_extractor.iter_rows, recalls_transformer.transform),
    "patient_alert": (
        patient_alerts_extractor.iter_rows,
        patient_alerts_transformer.transform,
    ),
    "communication": (
        communications_extractor.iter_rows,
        communications_transformer.transform,
    ),
}

_DEFAULT_ORDER: list[str] = [
    "catalog_item",
    "center",
    "professional",
    "user",
    "work_calendar",
    "work_calendar_day",
    "work_calendar_shift",
    "client",
    "patient",
    "patient_client_link",
    "appointment_recurrence",
    "appointment",
    "treatment_catalog_item",
    "treatment_catalog_variant",
    "treatment_phase_template",
    "budget",
    "budget_line",
    "applied_treatment",
    "applied_treatment_phase",
    "debt",
    "payment",
    "debt_payment_application",
    "fiscal_document",
    "fiscal_document_line",
    "pharmacological_history",
    "prescription",
    "prescription_item",
    "consent",
    "patient_document",
    "recall",
    "patient_alert",
    "communication",
]


class GesdenAdapter(OriginAdapter):
    """Origin adapter for Gesdén SQL Server databases."""

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
            id_mapping=id_mapping or IdMapping(),
            warnings=warnings or WarningRegistry(),
        )

    def connect(
        self,
        dsn: str,
        *,
        user: str | None = None,
        password: str | None = None,
        trusted_connection: bool = False,
        trust_server_certificate: bool = False,
        encrypt: bool = True,
    ) -> None:
        self._conn = connect(
            dsn,
            user=user,
            password=password,
            trusted_connection=trusted_connection,
            trust_server_certificate=trust_server_certificate,
            encrypt=encrypt,
        )

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

        pipeline = _SIMPLE_ENTITY_PIPELINE.get(entity_type)
        if pipeline is None:
            raise KeyError(f"Gesdén adapter does not support entity {entity_type!r}")
        iter_rows, transform = pipeline
        conn = self._require_conn()
        for row in iter_rows(conn):
            canonical = transform(row, self._ctx)
            self._ctx.id_mapping.register(
                self._ctx.source_system, canonical.entity_type, canonical.source_id
            )
            yield canonical

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def context(self) -> TransformContext:
        return self._ctx

    def _iter_catalog_items(self) -> Iterator[BaseCanonicalEntity]:
        conn = self._require_conn()
        for spec in catalogs_extractor.CATALOG_SPECS:
            for row in catalogs_extractor.iter_rows(conn, spec):
                canonical = catalogs_transformer.transform(row, self._ctx, spec=spec)
                self._ctx.id_mapping.register(
                    self._ctx.source_system, canonical.entity_type, canonical.source_id
                )
                yield canonical

    def _require_conn(self) -> pyodbc.Connection:
        if self._conn is None:
            raise RuntimeError("GesdenAdapter is not connected — call connect() first")
        return self._conn
