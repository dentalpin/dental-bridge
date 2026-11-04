"""Stable structural fingerprint for a Nemodent Access database."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    import pyodbc

_FINGERPRINT_COLUMNS: dict[str, tuple[str, ...]] = {
    "APPOINTMENT_DURATIONS": APPOINTMENT_DURATION_COLUMNS,
    "APPOINTMENT_SLOT_PERSONNEL": ("GUID_APPOINTMENT", "GUID_SLOT", "PersonnelID"),
    "APPOINTMENT_SLOTS": (
        "GUID",
        "GUID_APPOINTMENT",
        "StartTime",
        "EndTime",
        "LocationID",
        "Subject",
        "Description",
        "TASK_GUID",
    ),
    "APPOINTMENT_STATUS": APPOINTMENT_STATUS_COLUMNS,
    "APPOINTMENT_TYPES": APPOINTMENT_TYPE_COLUMNS,
    "APPOINTMENTS": (
        "GUID",
        "GUID_PATIENT",
        "GUID_ADMISSION",
        "GUID_TYPE",
        "EXTERNAL_ID",
        "Date",
        "StartTime",
        "EndTime",
        "Status",
        "ResponsiblePersonnel",
        "LocationID",
        "Subject",
        "Description",
        "Emergency",
        "Flags",
        "ModificationDate",
    ),
    "CLINIC": CENTER_COLUMNS,
    "CLINIC_LOCATIONS": CLINIC_LOCATION_COLUMNS,
    "CLINIC_LOCATION_TYPES": CLINIC_LOCATION_TYPE_COLUMNS,
    "ESTIMATES": BUDGET_COLUMNS,
    "ESTIMATES_PROCEDURES": BUDGET_LINE_COLUMNS,
    "INVOICE_DETAILS": FISCAL_DOCUMENT_LINE_COLUMNS,
    "INVOICE_HEADING": FISCAL_DOCUMENT_COLUMNS,
    "MASTER_PROCEDURE_TYPES": MASTER_PROCEDURE_TYPE_COLUMNS,
    "MASTER_PROCEDURES": MASTER_PROCEDURE_COLUMNS,
    "PATIENT_FOLLOWUP": (
        "GUID_APPOINTMENT",
        "GUID_PATIENT",
        "CheckInDate",
        "CheckInDelay",
        "CheckInTime",
        "CheckOutDelay",
        "CheckOutTime",
        "AdministrationTimeSpent",
        "TreatmentTimeSpent",
        "WaitingRoomTimeSpent",
        "TotalDelay",
        "TotalTimeSpent",
    ),
    "PATIENT_HISTORY": (
        "GUID",
        "GUID_PATIENT",
        "Date",
        "Comments",
        "GUID_SESSION",
        "Order",
        "RegionType",
        "Region",
        "Region2",
        "SubRegions",
    ),
    "PATIENT_PROCEDURES": (
        "GUID",
        "ProcedureID",
        "Class",
        "PersonnelID",
        "Personnel1ID",
        "Personnel2ID",
        "Amount",
        "Discount",
        "Debit",
        "InsuranceAmount",
        "Deposit",
        "Phase",
        "VAT",
    ),
    "PATIENT_TASKS": ("GUID", "TaskCode", "Status", "EndDate", "GUID_PARENT"),
    "PATIENT_TASKS_TRACING": PATIENT_TASK_TRACING_COLUMNS,
    "Patient": PATIENT_COLUMNS,
    "PatientAlerts": PATIENT_ALERT_COLUMNS,
    "PERSONNEL": PROFESSIONAL_COLUMNS,
    "PROCEDURES": PROCEDURE_COLUMNS,
}


def compute_fingerprint(conn: pyodbc.Connection) -> str:
    """Hash metadata for tables used by the adapter; no cell values are read."""
    return _fingerprint_connection(conn)


def _fingerprint_connection(conn: Any) -> str:
    table_cursor = conn.cursor()
    try:
        table_rows = table_cursor.tables(tableType="TABLE").fetchall()
    finally:
        table_cursor.close()

    available_tables_by_casefold = _available_tables_by_casefold(table_rows)
    table_entries = sorted(
        (
            (expected_name, available_tables_by_casefold[expected_name.casefold()])
            for expected_name in _FINGERPRINT_COLUMNS
            if expected_name.casefold() in available_tables_by_casefold
        ),
        key=lambda entry: entry[0].casefold(),
    )
    if not table_entries:
        raise ValueError("Access database exposes no Nemodent adapter tables")

    hasher = hashlib.sha256()
    for expected_table, actual_table in table_entries:
        hasher.update(_canonical_line("table", expected_table))
        column_cursor = conn.cursor()
        try:
            for expected_column in _FINGERPRINT_COLUMNS[expected_table]:
                columns = column_cursor.columns(
                    table=actual_table,
                    column=expected_column,
                ).fetchall()
                ordered_columns = sorted(
                    columns,
                    key=lambda row: int(_value(row, "ordinal_position", 16) or 0),
                )
                if not ordered_columns:
                    hasher.update(
                        _canonical_line("missing_column", expected_table, expected_column)
                    )
                    continue
                for column in ordered_columns:
                    values = (
                        str(_value(column, "column_name", 3)),
                        str(_value(column, "data_type", 4)),
                        str(_value(column, "type_name", 5)),
                        _optional_int(_value(column, "column_size", 6)),
                        _optional_int(_value(column, "decimal_digits", 8)),
                        _optional_int(_value(column, "nullable", 10)),
                        _optional_int(_value(column, "ordinal_position", 16)),
                    )
                    hasher.update(_canonical_line("column", expected_table, *values))
        finally:
            column_cursor.close()
    return f"sha256:{hasher.hexdigest()}"


def _available_tables_by_casefold(table_rows: list[Any]) -> dict[str, str]:
    return {
        table_name.casefold(): table_name
        for table_name in (
            str(_value(row, "table_name", 2))
            for row in table_rows
            if str(_value(row, "table_type", 3)).strip().upper() == "TABLE"
            and not _is_system_table(str(_value(row, "table_name", 2)))
        )
    }


def _value(row: Any, attribute: str, index: int) -> Any:
    """Read a pyodbc metadata field by name, with positional fallback for drivers."""
    try:
        return getattr(row, attribute)
    except AttributeError:
        return row[index]


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _canonical_line(*values: object) -> bytes:
    return (json.dumps(values, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _is_system_table(name: str) -> bool:
    upper = name.upper()
    return upper.startswith(("MSYS", "USYS", "~"))
