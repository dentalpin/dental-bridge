"""Streaming projection of Nemodent appointments, slots and assigned staff."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pyodbc

_RESULT_COLUMNS = (
    "AppointmentGUID",
    "PatientGUID",
    "AdmissionGUID",
    "AppointmentTypeGUID",
    "ExternalID",
    "AppointmentDate",
    "HeaderStart",
    "HeaderEnd",
    "AppointmentStatus",
    "ResponsiblePersonnel",
    "HeaderLocation",
    "HeaderSubject",
    "HeaderDescription",
    "Emergency",
    "Flags",
    "ModificationDate",
    "SlotGUID",
    "SlotStart",
    "SlotEnd",
    "SlotLocation",
    "SlotSubject",
    "SlotDescription",
    "SlotTaskGUID",
    "SlotPersonnelAppointmentGUID",
    "SlotPersonnel",
    "FollowupAppointmentGUID",
    "FollowupPatientGUID",
    "FollowupCheckInDate",
    "FollowupCheckInDelay",
    "FollowupCheckInTime",
    "FollowupCheckOutDelay",
    "FollowupCheckOutTime",
    "FollowupAdministrationTimeSpent",
    "FollowupTreatmentTimeSpent",
    "FollowupWaitingRoomTimeSpent",
    "FollowupTotalDelay",
    "FollowupTotalTimeSpent",
)

_APPOINTMENT_QUERY = """
SELECT
    a.[GUID] AS [AppointmentGUID],
    a.[GUID_PATIENT] AS [PatientGUID],
    a.[GUID_ADMISSION] AS [AdmissionGUID],
    a.[GUID_TYPE] AS [AppointmentTypeGUID],
    a.[EXTERNAL_ID] AS [ExternalID],
    a.[Date] AS [AppointmentDate],
    a.[StartTime] AS [HeaderStart],
    a.[EndTime] AS [HeaderEnd],
    a.[Status] AS [AppointmentStatus],
    a.[ResponsiblePersonnel] AS [ResponsiblePersonnel],
    a.[LocationID] AS [HeaderLocation],
    a.[Subject] AS [HeaderSubject],
    a.[Description] AS [HeaderDescription],
    a.[Emergency] AS [Emergency],
    a.[Flags] AS [Flags],
    a.[ModificationDate] AS [ModificationDate],
    s.[GUID] AS [SlotGUID],
    s.[StartTime] AS [SlotStart],
    s.[EndTime] AS [SlotEnd],
    s.[LocationID] AS [SlotLocation],
    s.[Subject] AS [SlotSubject],
    s.[Description] AS [SlotDescription],
    s.[TASK_GUID] AS [SlotTaskGUID],
    sp.[GUID_APPOINTMENT] AS [SlotPersonnelAppointmentGUID],
    sp.[PersonnelID] AS [SlotPersonnel],
    pf.[GUID_APPOINTMENT] AS [FollowupAppointmentGUID],
    pf.[GUID_PATIENT] AS [FollowupPatientGUID],
    pf.[CheckInDate] AS [FollowupCheckInDate],
    pf.[CheckInDelay] AS [FollowupCheckInDelay],
    pf.[CheckInTime] AS [FollowupCheckInTime],
    pf.[CheckOutDelay] AS [FollowupCheckOutDelay],
    pf.[CheckOutTime] AS [FollowupCheckOutTime],
    pf.[AdministrationTimeSpent] AS [FollowupAdministrationTimeSpent],
    pf.[TreatmentTimeSpent] AS [FollowupTreatmentTimeSpent],
    pf.[WaitingRoomTimeSpent] AS [FollowupWaitingRoomTimeSpent],
    pf.[TotalDelay] AS [FollowupTotalDelay],
    pf.[TotalTimeSpent] AS [FollowupTotalTimeSpent]
FROM ((([APPOINTMENTS] AS a
LEFT JOIN [APPOINTMENT_SLOTS] AS s
    ON a.[GUID] = s.[GUID_APPOINTMENT])
LEFT JOIN [APPOINTMENT_SLOT_PERSONNEL] AS sp
    ON s.[GUID] = sp.[GUID_SLOT])
LEFT JOIN [PATIENT_FOLLOWUP] AS pf
    ON a.[GUID] = pf.[GUID_APPOINTMENT])
ORDER BY a.[GUID], s.[GUID], sp.[PersonnelID]
"""


def iter_joined_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    """Yield one row per appointment slot/personnel pair, including empty slots."""
    cursor = conn.cursor()
    try:
        cursor.arraysize = 1000
        cursor.execute(_APPOINTMENT_QUERY)
        while batch := cursor.fetchmany(1000):
            for row in batch:
                yield dict(zip(_RESULT_COLUMNS, row, strict=True))
    finally:
        cursor.close()
