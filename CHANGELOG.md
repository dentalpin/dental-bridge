# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- **Patient-level free-text notes** are now extracted from
  ``Pacientes.Notas`` into ``CanonicalPatient.notes``. Spanish dental
  clinics keep ~46 % of their anamnesis, allergies and observations in
  this column (alongside the ``AlertPac`` popup table). Downstream
  importers can now mirror it into their clinical-notes store and
  classifiers; previously the whole column was dropped. Bumps the
  Gesdén ``ADAPTER_VERSION`` to ``0.0.2`` to mark the schema change.

### Fixed (continued)

- **Appointment status mapping (``DCitas.IdSitC``) had four wrong
  entries.** The previous map sent the dominant Gesdén status
  ``5`` (Finalizada — treatment done) to ``CANCELLED``,
  ``1`` (Anulada — cancelled) to ``SCHEDULED``, ``4`` (Consulta) to
  ``NO_SHOW``, and only covered five of the eleven catalog codes.
  On the live export that flipped ~57 k attended appointments into
  "cancelled" in the destination and the 48 k actually-cancelled
  ones into "scheduled". The map is now validated against the live
  ``TSitCita`` table (0 Planificada → SCHEDULED, 1 Anulada →
  CANCELLED, 2 Recepción / 3 Sala Espera / 7 Confirmada / 9 Enviado
  → CONFIRMED, 4 Consulta / 5 Finalizada / 8 Encuesta → ATTENDED,
  6 Fallada → NO_SHOW, 10 Anulada WhatsApp → CANCELLED). A
  parametrised test pins every entry plus the ``None`` /
  out-of-range fallback to ``UNKNOWN``.
- **TUsuAgd-derived professionals carry their label as Apellidos.**
  The extractor unions ``TUsuAgd`` rows when ``TColabos.IdCol`` is
  unset; the Descripcio column (a single-string identifier like
  "MARTINEZ SALMERON" or "DRA. VAZQUEZ") was being routed to
  ``Nombre``, which meant the destination user landed as
  ``first_name="MARTINEZ SALMERON" last_name="—"``. Routing it to
  ``Apellidos`` instead gives the conventional Spanish
  ``first_name="Profesional" last_name="MARTINEZ SALMERON"`` shape.

### Added

- **Odontogram decoder for Gesdén ``PiezasAdu`` / ``PiezasLec``.** The
  canonical ``applied_treatment`` and ``budget_line`` entities now
  expose ``teeth: list[int]`` carrying the FDI numbers decoded from
  the 32-bit per-tooth bit-masks. The mapping was reverse-engineered
  from frequency analysis against ``SOURCE_DB`` — the four top
  ``IdTipoOdg=24`` (implant) bit positions land on the four first
  molars (FDI 16/26/36/46), which is the dominant implant target in
  the dental literature. Quadrants are laid out 0-7 (UR 18→11),
  8-15 (UL 21→28), 16-23 (LR 48→41), 24-31 (LL 31→38); deciduous
  mirrors the same shape in quadrants 5/6/8/7. Surface decoding
  (``ZonasPieza``) is intentionally left for a follow-up pass —
  attempting it without UI validation would silently corrupt the
  destination odontogram. Validated against the real DB:
  64,318/252,937 applied treatments (25 %) and 119,078/385,074
  budget lines (31 %) now carry decoded teeth.

### Fixed

- **Gesdén appointment owner now resolves for ~100% of slots.** Before
  this fix `DCitas.IdCol` (the optional second-collaborator field)
  was used to derive `professional_uuid`; in real clinics IdCol is
  empty for ~96% of appointments, leaving most importable rows orphan.
  The transformer now derives the professional from `DCitas.IdUsu`
  (the column-owner / TUsuAgd FK, per `docs/schema_map.md`). To make
  every IdUsu resolvable, the professional extractor now unions
  `TColabos` with the subset of `TUsuAgd` rows that lack an `IdCol`
  link, emitting them as canonical professionals with `source_id =
  "usuagd:<IdUsu>"`. Validated end-to-end against the real SOURCE_DB:
  appointments with both patient and professional refs rose from
  4,544 (3.3%) to 109,654 (79.3%); the remaining 28,607 are calendar
  blocks with `IdPac IS NULL` (legitimately patient-less).

## [0.1.0] — 2026-05-14

First public release. The full migration loop from a live Gesdén
database to a portable DPMF file is functional and has been validated
against a real SOURCE_DB clinic dataset (1.27 million rows across
32 canonical entity types).

### Added — CLI modes

- `analyze` — read-only inventory, risk detection and HTML report. No
  DPMF written.
- `plan` — YAML scope plan emission from the live source.
- `extract` — produce a DPMF file. Optional `--compress` (zstd) and
  `--dpmf-passphrase` (AES-256-GCM).
- `verify` — reconcile a DPMF against its source. PASS/FAIL exit code
  and HTML report including the file's SHA-256 integrity hash.

### Added — Canonical model

- 32 entity types covering catalogues, organisational structure,
  patients and clients, work calendars, appointments, treatments
  applied and budgeted, financial documents, payments, debts,
  prescriptions, consents, attached documents, recalls, alerts and
  communications.
- Stable `canonical_uuid` derived as UUIDv5 over
  `(source_system, entity_type, source_id)` under a fixed namespace,
  guaranteeing idempotent re-extractions.
- Verbatim `raw_source_data` on every row for downstream auditability.

### Added — Gesdén adapter

- pyodbc connection layer with autodetect of ODBC Driver 18 and a
  friendly install-link error if missing.
- Schema fingerprint over `sys.tables` + `sys.columns` so adapters
  refuse to silently process unknown variants.
- Date/time decoders for the OLE epoch (`Fecha`) and seconds-since-
  midnight (`Hora`, `Duracion`) conventions used by Gesdén.
- UTF-8 decoding for SQL_CHAR columns (ODBC Driver 18 default), so
  Spanish accented characters round-trip cleanly.

### Added — Pipeline

- Topological-order extraction runner with rich progress UI.
- Self-FK and cross-table reference validation, with orphan
  nullification and warning emission.
- Resumable checkpoint store backed by SQLite, located at
  `%APPDATA%\dental-bridge\state.db` on Windows (and the equivalent
  user data directory on macOS/Linux).

### Added — DPMF format

- Format specification frozen at v0.1.0 (`spec/dpmf-v0.1.md`).
- Three on-disk forms: raw SQLite, zstd-compressed, and DPME-encrypted
  (AES-256-GCM with scrypt-derived key). The reader auto-detects which
  layers wrap the SQLite via magic-byte sniffing.
- Logical-content integrity hash so tampering is detectable
  independently of the storage layout.

### Added — Distribution

- `pyproject.toml` packaged with `uv`; PyInstaller spec at
  `build/dental-bridge.spec` produces a single Windows .exe.
- `.github/workflows/ci.yml`: lint, type-check, unit tests on Linux;
  PyInstaller smoke build on Windows for every push to `main` and PR.
- `.github/workflows/release.yml`: on a `v*.*.*` tag, builds the
  Windows binary, computes SHA-256, drafts a GitHub Release with the
  CHANGELOG entry, attaches the `.exe` and `.sha256` files.
- Operator guide for Windows: `docs/windows-deployment.md`.
- Legal framing: `NOTICE.md`, `TERMS.md`, `legal/INTEROPERABILITY.md`.

### Known limitations

- Binaries are **not** code-signed. Windows SmartScreen will warn on
  first run; verify the SHA-256 from the release notes before trusting.
- Image and document binaries (radiographs, scanned PDFs) are
  catalogued in `_files` but not transferred; the v0.2 sync agent will
  handle them.
- Odontogram decoding is deferred — the raw Gesdén bit-mask columns are
  preserved verbatim, and an importer that needs them can decode them
  itself. Empirical validation against the Gesdén UI is needed first.
- Single Gesdén schema fingerprint registered. Clinics on customised
  variants need to file an issue with their fingerprint so we can
  publish the corresponding entry.
