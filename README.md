# dental-bridge

> Open source migration toolkit for dental practice management systems.
> First connector: **Gesdén**. Reference destination: **Dentalpin**.
> Output format: **DPMF — Dental Practice Migration Format** (open standard).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: Pre-Alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)](#status)
[![Windows](https://img.shields.io/badge/platform-windows-blue.svg)](#requirements)

## What it does

`dental-bridge` reads the SQL Server database of a Gesdén installation
(running on the clinic's Windows server) and produces a single portable file
that any downstream PMS can ingest. No data leaves the clinic until the
file is uploaded to a destination of the operator's choice.

```
┌──────────────┐    extract     ┌──────────────┐    upload     ┌──────────────┐
│  Gesdén DB   │ ─────────────► │  clinica.dpm │ ────────────► │   Any PMS    │
│  (SQL Server)│                │   (DPMF v0.1)│               │   importer   │
└──────────────┘                └──────────────┘               └──────────────┘
                                       +
                                clinica-files
                                .manifest.json
                                (image refs)
```

The toolkit is structured as a pluggable extractor: today Gesdén, tomorrow any
other PMS. The output format is a versioned open specification, not a
proprietary protocol.

## Status

**v0.1.0 — first public release.** The CLI is feature-complete for
Gesdén-to-DPMF migration: 32 canonical entity types, four operating
modes (`analyze` / `plan` / `extract` / `verify`), zstd compression and
AES-256-GCM encryption layers, validated against a 1.27-million-row
real clinic dataset.

Binaries are distributed **unsigned**. Windows SmartScreen will warn on
first run; verify the SHA-256 published in the release notes against
`Get-FileHash` before trusting. See `docs/windows-deployment.md` for
the full SmartScreen flow.

## Download

Pre-built Windows binaries: <https://github.com/dentalpin/dental-bridge/releases>.

Each release ships:

- `dental-bridge-<version>-windows-x64.exe` — the executable.
- `dental-bridge-<version>-windows-x64.exe.sha256` — companion hash file.

Verify before running:

```powershell
Get-FileHash .\dental-bridge-0.1.0-windows-x64.exe -Algorithm SHA256
Get-Content .\dental-bridge-0.1.0-windows-x64.exe.sha256
```

The two digests MUST match. If they do not, do not run the binary.

## Requirements

**Runtime (clinic side):**
- Windows Server 2012 R2 or later, or Windows 10/11.
- Microsoft ODBC Driver 18 for SQL Server (installer will detect and prompt).
- Read access to the Gesdén SQL Server instance (SQL Auth or Windows Auth).

**Development:**
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management.
- Docker (only for running tests against a local Gesdén copy).

## Quick start (CLI)

```powershell
# 1. Analyse — read-only inspection, no changes
dental-bridge analyze --source "gesden://server\SQLEXPRESS/SOURCE_DB" --user sa

# 2. Plan — generate a YAML scope file you can edit
dental-bridge plan --source "gesden://..." --output plan.yaml

# 3. Extract — produce the DPMF file
dental-bridge extract --source "gesden://..." --plan plan.yaml --output clinica.dpm

# 4. Verify — reconciliation report (counts, financial totals, sampled deep-diff)
dental-bridge verify --source "gesden://..." --file clinica.dpm
```

After extract, you can upload `clinica.dpm` to any PMS that supports the
DPMF format. See `spec/dpmf-v0.1.md` for the format specification.

## Development setup

```bash
# Clone
git clone https://github.com/dentalpin/dental-bridge.git
cd dental-bridge

# Install with uv
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check
uv run ruff format --check

# Bring up a local Gesdén database for integration testing
./scripts/bootstrap.sh        # uses docker-compose with SQL Server 2022
```

See `docs/` for architecture and `CONTRIBUTING.md` for the contribution
workflow including DCO sign-off.

## Adding a new origin adapter

Want to migrate from a PMS other than Gesdén? Implement an
`OriginAdapter` subclass under `src/dental_bridge/adapters/<your_pms>/`.
See `docs/adapter-authoring.md` for the full guide.

## Image and attachment handling

`dental-bridge` produces a `clinica-files.manifest.json` alongside the DPMF
file listing every image/document referenced by the data, with SHA-256
checksums and relative paths. The binaries themselves are not bundled —
they are typically large (radiographs in DICOM/PNG can total hundreds of GB)
and a separate sync agent handles their upload to the destination's storage.
This separation keeps the DPMF file small and inspectable.

## DPMF — the format

DPMF is a SQLite-based container, optionally zstd-compressed and AES-256-GCM
encrypted. Every entity has a stable `canonical_uuid`, a `source_id` from the
origin system, and a `raw_source_data` payload preserving the original row
exactly as extracted. The format is versioned via SemVer; importers declare
the version range they support.

Full specification: [`spec/dpmf-v0.1.md`](spec/dpmf-v0.1.md).

## License and legal framework

`dental-bridge` is distributed under the [Apache License 2.0](LICENSE).
It is published free of charge to enable lawful interoperability between
dental practice management systems under EU Directive 2009/24/EC art. 6
and Spanish Intellectual Property Law art. 100.5.

The toolkit is not commercialised, is not affiliated with Infomed S.A.
(producer of Gesdén), and contains no copy of any third-party PMS code,
binary, asset or documentation. References to "Gesdén" in this
repository are strictly nominative — necessary to identify the system
this toolkit interoperates with.

For the full framing, please read:

- [`NOTICE.md`](NOTICE.md) — attributions and scope of liability.
- [`TERMS.md`](TERMS.md) — operator's terms of use (authorisation,
  data-protection compliance, lawful interoperability).
- [`legal/INTEROPERABILITY.md`](legal/INTEROPERABILITY.md) — what the
  schema-discovery work covers and what it explicitly excludes.

If you represent a rights holder and have a good-faith concern about
content in this repository, please contact legal@dentalpin.com.

## Project sponsor

This project is sponsored and initially maintained by
[Dentalpin](https://dentalpin.com). Dentalpin is the reference destination
implementation; any PMS vendor is welcome to publish their own DPMF
importer. The DPMF format itself is an open standard.

## Reference: development database

The development environment runs a Gesdén `SOURCE_DB.MDF` file inside SQL
Server 2022 via Docker for testing the extractor end-to-end. The clinical
database files (`bbdd/`, `data/`) are **never** committed to this repository.
See `scripts/bootstrap.sh` for the local stack and `docs/migration_order.md`,
`docs/schema_map.md`, `docs/odontograma_decoding.md` for the
reverse-engineering notes.
