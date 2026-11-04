# Nemodent adapter notes

The Nemodent adapter reads a local Microsoft Access `.mdb` copy and emits
the supported DPMF v0.1 entities. It supports `dental-bridge extract` only;
the Gesdén-specific `analyze`, `plan` and `verify` flows are not generalized.

## Connection and schema safety

- The Access connection is read-only. The adapter does not write to the MDB.
- Extraction reads explicit allowlisted columns; it never uses `SELECT *`.
- The schema fingerprint covers adapter-relevant table/column metadata only.
  It does not inspect patient rows or hash cell values.
- Unknown fingerprints block extraction unless the operator explicitly uses
  `--allow-unknown-schema`.
- A 64-bit Access ODBC driver is required for the Windows x64 build.

## Mapping decisions

- Appointment source IDs use source appointment/slot/personnel keys where
  needed to identify an expanded source row. Professional references remain
  canonical foreign references; no destination UUID is used as `source_id`.
- Within one export, if two active appointments resolve to the same
  chair/professional/date/time tuple, the adapter keeps the first in stable
  source order and omits later rows with
  `appointment.duplicate_slot_omitted`. Appointments for different
  professionals remain separate. This cannot detect collisions with
  appointments already present in a destination clinic.
- Every `PATIENT_TASKS_TRACING` row is emitted as an applied-treatment phase.
  `TraceCount` remains in `raw_source_data`; its meaning is not confirmed.
- `PATIENT_PROCEDURES` rows are kept even without a matching history row.
  Missing history is reported as a warning; unresolved patient/date fields
  remain null rather than being inferred.
- For treatment and budget lines, `Amount` is the unit price and `Discount` is
  a percentage. Applied-treatment `Debit` is the pending amount; budget-line
  `Debit` remains raw because the canonical budget line has no pending field.
- `Patient.GUID_ACCOUNT_HOLDER` identifies the payer. If it is empty and
  `Holder` marks the patient as the account holder, `GUID_ACCOUNT` is the
  fallback. Client entities are not emitted while `DocumentType` codes remain
  unknown.
- Accounting tables are not reinterpreted as payments or debt. Recalls are
  excluded until their patient key and future-record semantics are confirmed.
- Document references are preserved, but `_files` entries are not emitted
  without a verified external document root and lookup rule.

These are conservative v1 boundaries, not claims that the source system lacks
those data. Unmapped values remain in `raw_source_data` when the entity is
otherwise exported.

## Local verification

The Access integration test is opt-in and requires a sanitized or synthetic
MDB:

```powershell
$env:NEMODENT_TEST_MDB = "C:\Fixtures\nemodent-sanitized.mdb"
uv run pytest -m integration tests/integration/test_nemodent_access_readonly.py
```

Never commit a production MDB or patient export.
