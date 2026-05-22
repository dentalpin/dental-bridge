# TColabos / TUsuAgd / TUsers — observed schema

Inspected on the live MDF (`bbdd/SOURCE_DB.MDF`) via `gesden-mssql` container.

## TColabos — 65 rows

Deactivation / role signals:

| Column | Type | NULL | Meaning |
|--------|------|------|---------|
| `Activo` | `char(1)` | NOT NULL | `'S'` = active, `'N'` = inactive |
| `FecBaja` | `smalldatetime` | nullable | Date the collaborator left the clinic. Non-NULL ⇒ inactive |
| `IdTipoColab` | `int` | nullable | Role: `1`=doctor (DentalPin dentist), `2`=hygienist, `3`=auxiliary, `4`=admin. In this MDF: 58 rows with `1`, 7 with `NULL`. |
| `FecAlta` | `smalldatetime` | nullable | Hire date |

Active counts in this MDF:

- `Activo='S'`: **31** rows
- `Activo='S' AND has TtosMed activity in last 24 months`: **22** rows
- `FecBaja IS NOT NULL`: **34** rows

## TUsuAgd — 20 rows (agenda columns)

| Column | Type | NULL | Meaning |
|--------|------|------|---------|
| `Status` | `int` | nullable | `1` = active agenda column, `0` = inactive |
| `IdCol` | `int` | nullable | FK to `TColabos.IdCol`. **18 of 20 rows have `NULL`** (orphans). |
| `Descripcio` | `varchar` | nullable | Single label shown in agenda (often surname, sometimes "DRA. APELLIDO") |
| `IdCentro` | `int` | nullable | Clinic center |

Distribution:

- `Status=1`: **14** rows
- `Status=0`: **6** rows
- `IdCol IS NULL` (orphans): **18** rows

## TUsers — 42 rows (system login accounts)

Columns of note: `IdUser`, `Login`, `Nombre`, `Apellidos`, `NIF`, `Email`, `IdCol` (FK to `TColabos`).

No `Activo` / `FecBaja` column observed. Activity inference would have to come from login audit if available.

## Implication for the migration

| Signal | Source | DentalPin canonical field |
|--------|--------|---------------------------|
| Source-marked inactive | `TColabos.Activo='N'` OR `TColabos.FecBaja IS NOT NULL` | `CanonicalProfessional.deactivated = True` |
| Agenda column inactive | `TUsuAgd.Status=0` | `CanonicalProfessional.deactivated = True` |
| Agenda orphan | `TUsuAgd.IdCol IS NULL` | `source_id` starts with `usuagd:` — mapper can soft-filter |
| Activity proxy | `MAX(TtosMed.FecIni, Presu.FecPresup, Recalls.Fecha, DCitas.FecAlta)` per `IdCol` | `CanonicalProfessional.last_activity_at` |
| Activity for TUsuAgd | `MAX(DCitas.FecAlta)` where `DCitas.IdUsu = TUsuAgd.IdUsu` | same |

`DCitas.Fecha` is encoded as a Gesdén integer (decoded elsewhere in the bridge); for activity-window detection we use `DCitas.FecAlta` (the row-insertion smalldatetime) which is good enough for "did this professional have any traffic recently".
