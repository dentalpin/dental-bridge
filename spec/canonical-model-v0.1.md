# Canonical model — v0.1 (draft)

> Status: **draft**. The canonical model is the PMS-agnostic representation
> that origin adapters target and DPMF importers consume. Each entity has
> its own SemVer recorded in the `_entities` table of the DPMF file.

## Conventions

- All IDs in the canonical model are UUIDs (v5) derived deterministically
  from the source system's primary key. Foreign references between
  canonical entities use these UUIDs.
- Dates and times are ISO-8601 strings in UTC unless explicitly typed
  as local civil time (e.g. an appointment's clinic-local start).
- Monetary amounts use a `Decimal` (string-serialised in JSON) plus an ISO
  4217 currency code.
- Every entity inherits the envelope defined in
  `dental_bridge.core.canonical.base.BaseCanonicalEntity` and therefore
  carries `canonical_uuid`, `source_system`, `source_id`,
  `adapter_version`, `extracted_at`, `raw_source_data`.

## Entities in v0.1

The list below mirrors the migration order documented for the Gesdén
adapter (see `docs/migration_order.md`). For each entity, this file will
ultimately define: required fields, optional fields, value domains,
referential integrity expectations, and per-field provenance notes when
the canonical value involves non-obvious decoding.

| Entity | Source-system example (Gesdén) | Notes |
|---|---|---|
| `Center` | `Centros` | Clinic / site / branch |
| `Professional` | `TColabos` | Doctor, hygienist, auxiliary staff |
| `Patient` | `Pacientes` | The clinical subject |
| `Client` | `Clientes` | The payer — may or may not equal the patient |
| `PatientClientLink` | `PacCli` | M:N relation patient ↔ payer |
| `WorkCalendar` | `TCalCa` + `TCalDias` + `TCalHor` | Center- and resource-level schedules |
| `Appointment` | `DCitas` | Including the integer date/time encoding |
| `AppointmentRecurrence` | `DCitasPeriod` | Series parent |
| `TreatmentCatalogItem` | `Tratamientos` + `Tratamientos_Tarifas` | Flattened with variants |
| `AppliedTreatment` | `TtosMed` | The clinical event |
| `AppliedTreatmentPhase` | `TtosMedFases` | Sessions of an applied treatment |
| `OdontogramEntry` | `TtosMed` (bit-mask columns) | Stored with raw fields; partial decoding only when validated |
| `Budget` | `Presu` | With self-FK alternatives |
| `BudgetLine` | `PresuTto` | Mutually referenced with `AppliedTreatment` |
| `Payment` | `PagoCli` | Immutable historical record |
| `Debt` | `DeudaCli` | |
| `DebtPaymentApplication` | `DeudaPago` | |
| `FiscalDocument` | `DocAdmin` | Preserves legal hashes (Verifactu / TicketBAI / ATCUD) |
| `FiscalDocumentLine` | `LinAdmin` | |
| `Recall` | `Recalls` | |
| `PatientAlert` | `AlertPac` | |
| `Document` | `TDocumentosPac` | References `_files` manifest entries |
| `Prescription` | `RecetasCab` | |
| `PrescriptionItem` | `RecetasDet` | |
| `Consent` | `TConsinCab` | Only the rendered form (not the key/value detail) |
| `PharmacologicalHistory` | `TTratamientos` | Distinct from the catalog table of the same root |
| `Communication` | `EdMail` + `EdMailL` + `PacMensajes` | Email and patient messages |

## Controlled vocabularies

Some canonical fields draw values from a controlled vocabulary defined in
YAML files under `src/dental_bridge/core/canonical/vocab/`. These vocabularies
have stable UUIDs per term so that mappings from a source system survive
renames or translations.

- `tooth_conditions.yaml` — clinical states of a tooth or surface.
- `tooth_surfaces.yaml` — anatomical surfaces (mesial, distal, occlusal, …).
- `notations.yaml` — tooth numbering systems (FDI, Universal, Palmer).

## Field-level specifications

To be populated entity by entity as Sprint 1 onwards builds the
corresponding Pydantic models.

### Debt

| Field | Type | Meaning |
|---|---|---|
| `opening_balance` | Optional boolean | `true` identifies a patient's net opening balance carried over from the source system. Absent or `false` denotes an ordinary debt row. |
| `description` | Optional string | Human-readable label for the debt or opening balance. Consumers may truncate it; DentalPin stores up to 160 characters. |

An opening balance uses the existing `owed_amount` field. Positive
amounts represent receivables and negative amounts represent credit.
An opening balance may be independent of any applied treatment. Use one
stable `canonical_uuid` per patient's opening balance so the same balance
can be recognized when the package is imported again.

### FiscalDocumentLine

A line may include a direct catalog reference even when it has no
`applied_treatment_uuid`.

| Field | Type | Target |
|---|---|---|
| `treatment_uuid` | Optional UUID | Canonical UUID of a `TreatmentCatalogItem` |
| `treatment_variant_uuid` | Optional UUID | Canonical UUID of a `TreatmentCatalogVariant` |

Both fields may be omitted or null. When both are provided, producers
should reference a treatment and one of its variants. Consumers may use
the catalog references to identify the service without deriving it from
an applied treatment. The line carries its billed concept, amounts and
taxes independently of the catalog.
