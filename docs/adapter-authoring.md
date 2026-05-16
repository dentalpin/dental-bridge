# Authoring a new origin adapter

> Status: **stub**. Will be expanded as the Gesdén adapter solidifies and
> serves as the reference implementation. Until then, treat
> `src/dental_bridge/adapters/gesden/` as the canonical example.

## Overview

An origin adapter is a Python subpackage that knows how to read a specific
PMS's database and yield canonical entities. The pipeline runner is
responsible for ordering, checkpointing and writing to DPMF — adapters
focus on the source.

## File layout

```
src/dental_bridge/adapters/<your_pms>/
├── __init__.py                # ADAPTER_NAME, ADAPTER_VERSION
├── adapter.py                 # YourAdapter(OriginAdapter)
├── connection.py              # auth, DSN handling, autodetect
├── schema_fingerprint.py      # how you hash the source schema
├── version_registry.py        # fingerprints you support
├── extractors/                # one module per entity, reads source rows
├── transformers/              # one module per entity, raw → canonical
└── decoders/                  # type-specific conversions (dates, encodings, bit-masks…)
```

## Mandatory pieces

1. Subclass `dental_bridge.core.adapters.origin_abc.OriginAdapter`.
2. Implement `connect`, `fingerprint`, `supported_entities`, `iter_entity`,
   `close`.
3. Register the class as a `dental_bridge.adapters` entry point in your
   distribution's `pyproject.toml`:
   ```toml
   [project.entry-points."dental_bridge.adapters"]
   your_pms = "dental_bridge.adapters.your_pms.adapter:YourAdapter"
   ```
4. Provide tests under `tests/unit/adapters/<your_pms>/`. Every transformer
   must have a table-driven test with at least the happy path and the most
   common edge cases.

## Reverse-engineering hygiene

This project does interoperability work only on source databases the user
owns and operates. We do not redistribute proprietary code, binaries or
schema dumps from third-party vendors. When you document a source system's
quirks (e.g. integer-encoded dates, bit-mask columns, sentinel values),
prefer describing the observable behaviour over speculating about internal
intent.

## What to do when the source is ambiguous

Two rules of thumb:

- **When unsure, preserve the source value in `raw_source_data` and emit a
  warning.** Don't guess. A downstream importer can decide later, with
  more context, what to do with an ambiguous field.
- **Document every assumption in code comments AND in
  `docs/<your_pms>-quirks.md`.** Future contributors (and you in six
  months) will need to know why a particular transformer behaves the way
  it does.

## Validation

Before opening a PR adding a new adapter, the following should all be
true:

- `uv run ruff check` passes.
- `uv run mypy src/dental_bridge/adapters/<your_pms>` passes.
- `uv run pytest tests/unit/adapters/<your_pms>` passes.
- The DPMF produced for a representative sample loads cleanly with
  `scripts/verify-dpmf.py`.
