# Contributing to dental-bridge

Thanks for considering a contribution. This document explains the workflow,
the legal sign-off, and what we expect from a well-formed contribution.

## Developer Certificate of Origin (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/)
(DCO) instead of a CLA. Every commit must be signed off:

```bash
git commit -s -m "feat(gesden): add IdCliTutor resolution"
```

The `-s` flag adds a `Signed-off-by: Name <email>` trailer to your commit
message. By doing so you certify that you wrote the code (or have the right
to submit it) under the project's Apache 2.0 License.

CI rejects unsigned commits on pull requests.

## Development setup

Prerequisites: Python 3.12+, [uv](https://github.com/astral-sh/uv), Docker
(for integration tests).

```bash
git clone https://github.com/dentalpin/dental-bridge.git
cd dental-bridge
uv sync --all-extras
uv run pytest
```

To run integration tests against a local Gesdén database:

```bash
./scripts/bootstrap.sh        # boots SQL Server 2022 + attaches sample DB
uv run pytest -m integration
```

## What kind of contributions we welcome

- **New origin adapters**: connectors for other dental PMS systems
  (Klinikare, OdontoNet, Klinic Cloud, etc.). See `docs/adapter-authoring.md`.
- **Bug fixes** in the Gesdén adapter, especially edge cases on different
  Gesdén versions. Open an issue first describing the symptom and the
  Gesdén version fingerprint.
- **Schema fingerprints** for Gesdén variants we haven't seen.
- **Documentation improvements**, especially around the DPMF spec and
  troubleshooting on Windows.
- **Test fixtures** (synthetic data, edge cases).

## What we do NOT accept

- Closed-source modules or proprietary destination loaders. Everything in
  this repo is Apache 2.0.
- Telemetry or analytics that runs without explicit opt-in.
- Code or fixtures derived from clinical data that has not been anonymised
  with appropriate legal basis. **Never commit a real patient row.**
- Reverse-engineered binaries or strings from Gesdén's own executables.
  This project's interoperability work is limited to inspecting database
  structure (table/column shapes, value semantics), not Gesdén code.
  See `legal/INTEROPERABILITY.md` for the precise scope.
- Stored-procedure, trigger, function or view bodies extracted from a
  Gesdén installation. These are Infomed-authored code and are out of
  scope regardless of whether they were technically accessible via
  `sys.sql_modules`.
- Screenshots, icons, fonts or any other media assets belonging to
  Gesdén, Infomed or their affiliates.
- Specific row-count statistics that could identify an individual
  clinic's volume. Use orders of magnitude where useful.

## Adding a new origin adapter

High level: subclass `OriginAdapter` from `dental_bridge.core.adapters` and
implement the abstract methods. Each adapter lives under
`src/dental_bridge/adapters/<pms_name>/` and is registered via
`pyproject.toml` entry points so the CLI discovers it.

Required components per adapter:

1. `connection.py` — how to authenticate and connect.
2. `schema_fingerprint.py` — how to detect which version of the source schema
   you're looking at.
3. `version_registry.py` — known fingerprints this adapter supports.
4. `extractors/<entity>.py` — one per canonical entity you produce.
5. `transformers/<entity>.py` — raw source row → canonical Pydantic model.
6. `decoders/` — type-specific decoders (date formats, encodings, bit-masks…).
7. Tests under `tests/unit/adapters/<pms_name>/` with synthetic fixtures.

Full walkthrough: [`docs/adapter-authoring.md`](docs/adapter-authoring.md).

## Coding standards

- Type-annotated Python; `mypy --strict` should pass.
- Format with `ruff format`, lint with `ruff check`.
- All public functions have docstrings explaining **why** the function is
  needed when the behaviour is non-obvious (encoding quirks, source-system
  workarounds, etc.). Skip docstrings for trivially self-evident code.
- Tests are required for every transformer and decoder. We prefer
  table-driven tests (a list of input → expected canonical output rows).

## Pull request workflow

1. Open an issue describing what you want to change. Wait for triage before
   investing significant time.
2. Fork, branch, commit with `-s` sign-off.
3. Open a PR against `main`. Fill out the template.
4. CI runs lint, type check, unit tests and (where possible) integration
   tests. Address feedback.
5. A maintainer merges with squash. We prefer one logical change per PR.

## Reporting security issues

Do **not** open a public GitHub issue for security vulnerabilities. Email
security@dentalpin.com or use a private GitHub security advisory.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be
respectful. Disagree in good faith.
