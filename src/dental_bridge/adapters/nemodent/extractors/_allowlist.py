"""Explicit source-column allowlists for Nemodent entity reads."""

from __future__ import annotations

CENTER_COLUMNS = (
    "GUID",
    "InternetID",
    "Name",
    "NIF",
    "Address",
    "Zip_Code",
    "City",
    "State",
    "CountryCode",
    "Phone1",
    "Mobile",
    "Email1Address",
)

CLINIC_LOCATION_COLUMNS = ("ID", "Name", "Type")
CLINIC_LOCATION_TYPE_COLUMNS = ("ID", "Name")
APPOINTMENT_STATUS_COLUMNS = ("ID", "Name")
APPOINTMENT_DURATION_COLUMNS = ("GUID", "Hour", "Min")
APPOINTMENT_TYPE_COLUMNS = (
    "GUID",
    "Name",
    "Description",
    "Color",
    "GUID_DURATION",
    "GROUP_ID",
)
MASTER_PROCEDURE_TYPE_COLUMNS = ("TypeID", "Name", "NemodentCode")
MASTER_PROCEDURE_COLUMNS = (
    "ID",
    "Description",
    "Amount",
    "TypeID",
    "NemodentCode",
    "IsDisabled",
)
PROCEDURE_COLUMNS = (
    "Class",
    "ID",
    "Code",
    "Description",
    "PatientAmount",
    "InsuranceAmount",
    "IsDisabled",
)
BUDGET_COLUMNS = (
    "GUID",
    "GUID_PATIENT",
    "PersonnelID",
    "Date",
    "EstimateNumber",
    "Name",
    "Comments",
    "Status",
    "Amount",
    "SubTotal",
    "Discount",
    "Taxes",
    "Total",
)
BUDGET_LINE_COLUMNS = (
    "GUID",
    "GUID_ESTIMATE",
    "GUID_PARENT",
    "ProcedureID",
    "Class",
    "Personnel1ID",
    "Personnel2ID",
    "Status",
    "Order",
    "Amount",
    "Debit",
    "Discount",
    "InsuranceAmount",
    "Deposit",
)
PATIENT_TASK_TRACING_COLUMNS = (
    "GUID_TASK",
    "Date",
    "StartTime",
    "EndTime",
    "Status",
    "TraceCount",
)
PATIENT_ALERT_COLUMNS = ("GUID", "Description", "Type")
FISCAL_DOCUMENT_COLUMNS = (
    "GUID",
    "GUID_HOLDER_ACCOUNT",
    "Date",
    "DocumentType",
    "InvoiceNumber",
    "SerieID",
    "Name",
    "NIF",
    "Address",
    "ZipCode",
    "SubTotal",
    "Taxes",
    "Total",
    "TotalVat",
    "Signature",
    "TickeBaiMessage",
    "TicketBaiStatus",
)
FISCAL_DOCUMENT_LINE_COLUMNS = (
    "GUID",
    "GUID_HEADING",
    "Class",
    "ProcedureID",
    "Description",
    "Quantity",
    "Amount",
    "TotalAmount",
    "VAT",
)

PROFESSIONAL_COLUMNS = (
    "ID",
    "First",
    "Surname",
    "NIF",
    "Type",
    "MembershipNumber",
    "Email1Address",
    "Phone1",
    "Mobile",
    "Fax",
    "InternetID",
)

PATIENT_COLUMNS = (
    "GUID",
    "GUID_ACCOUNT",
    "GUID_ACCOUNT_HOLDER",
    "GUID_REFERRER_PATIENT",
    "Holder",
    "CHN",
    "First",
    "SurName",
    "NIF",
    "BirthDate",
    "SexCode",
    "Phone1",
    "Mobile",
    "Fax",
    "Email1Address",
    "Address",
    "Zip_Code",
    "City",
    "State",
    "CountryCode",
    "Comments",
    "AdmissionDate",
    "ExternalCode",
    "GUID_CLINIC",
    "ID_PERSONNEL_DOCTOR",
    "ID_PERSONNEL_AUX",
)
