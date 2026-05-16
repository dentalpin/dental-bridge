# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
