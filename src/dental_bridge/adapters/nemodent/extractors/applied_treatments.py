"""Join Nemodent patient history, task and procedure rows for clinical events."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pyodbc

_RESULT_COLUMNS = (
    "ProcedureGUID",
    "HistoryGUID",
    "ProcedureID",
    "ProcedureClass",
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
    "PatientGUID",
    "HistoryDate",
    "HistoryComments",
    "HistorySessionGUID",
    "HistoryOrder",
    "HistoryRegionType",
    "HistoryRegion",
    "HistoryRegion2",
    "HistorySubRegions",
    "TaskCode",
    "TaskStatus",
    "TaskEndDate",
    "TaskParentGUID",
)

_APPLIED_TREATMENT_QUERY = """
SELECT
    pp.[GUID] AS [ProcedureGUID],
    ph.[GUID] AS [HistoryGUID],
    pp.[ProcedureID] AS [ProcedureID],
    pp.[Class] AS [ProcedureClass],
    pp.[PersonnelID] AS [PersonnelID],
    pp.[Personnel1ID] AS [Personnel1ID],
    pp.[Personnel2ID] AS [Personnel2ID],
    pp.[Amount] AS [Amount],
    pp.[Discount] AS [Discount],
    pp.[Debit] AS [Debit],
    pp.[InsuranceAmount] AS [InsuranceAmount],
    pp.[Deposit] AS [Deposit],
    pp.[Phase] AS [Phase],
    pp.[VAT] AS [VAT],
    ph.[GUID_PATIENT] AS [PatientGUID],
    ph.[Date] AS [HistoryDate],
    ph.[Comments] AS [HistoryComments],
    ph.[GUID_SESSION] AS [HistorySessionGUID],
    ph.[Order] AS [HistoryOrder],
    ph.[RegionType] AS [HistoryRegionType],
    ph.[Region] AS [HistoryRegion],
    ph.[Region2] AS [HistoryRegion2],
    ph.[SubRegions] AS [HistorySubRegions],
    pt.[TaskCode] AS [TaskCode],
    pt.[Status] AS [TaskStatus],
    pt.[EndDate] AS [TaskEndDate],
    pt.[GUID_PARENT] AS [TaskParentGUID]
FROM ([PATIENT_PROCEDURES] AS pp
LEFT JOIN [PATIENT_HISTORY] AS ph
    ON pp.[GUID] = ph.[GUID])
LEFT JOIN [PATIENT_TASKS] AS pt
    ON pp.[GUID] = pt.[GUID]
ORDER BY pp.[GUID]
"""


def iter_joined_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    """Yield one joined clinical event per Nemodent patient-procedure row."""
    cursor = conn.cursor()
    try:
        cursor.arraysize = 1000
        cursor.execute(_APPLIED_TREATMENT_QUERY)
        while batch := cursor.fetchmany(1000):
            for row in batch:
                yield dict(zip(_RESULT_COLUMNS, row, strict=True))
    finally:
        cursor.close()
