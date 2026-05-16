# Architecture

`dental-bridge` is a pipeline that extracts data from a dental PMS,
validates it against a PMS-agnostic canonical model, and writes the result
to a single portable file (the **DPMF** container) for downstream importers
to consume.

## High-level flow

```
┌──────────────────────────────────────────────────────────────┐
│  origin adapter                                              │
│     extractors  ─►  transformers  ─►  CanonicalEntity        │
└────────────────────────────────┬─────────────────────────────┘
                                 │
            ┌────────────────────▼────────────────────┐
            │ core pipeline                           │
            │   - topological runner                  │
            │   - id_mapping (source_id → uuid)       │
            │   - checkpoint (SQLite local state)     │
            │   - warning registry                    │
            └────────────────────┬────────────────────┘
                                 │
            ┌────────────────────▼────────────────────┐
            │ DPMF writer                             │
            │   - SQLite container                    │
            │   - optional zstd compression           │
            │   - optional AES-256-GCM encryption     │
            │   - integrity hash                      │
            └────────────────────┬────────────────────┘
                                 │
                       clinica.dpm  +  clinica-files.manifest.json
                                 │
                      ─────────► any DPMF-aware importer
```

## Why a file, not an HTTP push

The destination of a migration is a SaaS that will typically shard the
clinic into a tenant-specific database. Sending data row-by-row through an
HTTP API would require: per-tenant routing inside the API, async job
queueing per tenant, broad authentication scopes during the migration
window, and rate limiting carve-outs. By materialising the migration as a
file we avoid that complexity entirely — the importer runs in the
destination's own infrastructure, in the tenant's session context, with
the destination's own batching strategy.

Files are also offline-friendly (a clinic with slow connectivity can
generate the file overnight and upload it later), auditable (the file is
an artefact the clinic can archive as legal proof of what was migrated),
and reproducible (re-running the extractor on the same source yields a
file that can be diffed against the previous run).

## Why a canonical model

The intermediate canonical model decouples adapters from importers. A new
origin PMS only has to map onto the canonical entities; a new destination
PMS only has to consume them. We avoid an O(n×m) mesh of point-to-point
mappings.

The canonical model is conservative: when in doubt, we preserve the
original source row in `raw_source_data` instead of inventing fields. This
keeps the model small, reduces the risk of misrepresenting source
semantics, and lets importers fall back to the source payload when they
need information the canonical view does not surface.

## Critical invariants

- **Deterministic IDs**: every canonical row's `canonical_uuid` is a UUIDv5
  over `(source_system, source_id)`. Re-extracting yields the same UUIDs,
  which makes re-imports idempotent.
- **Provenance preserved**: every canonical row carries `raw_source_data`
  verbatim from the source. A bug in a transformer can be fixed by
  re-running with the corrected adapter against the same DPMF, without
  re-querying the source.
- **Topological extraction order**: entities are emitted in an order that
  respects foreign-key dependencies (catalogs first, then patients, then
  appointments, etc.). See `docs/migration_order.md` for the Gesdén-specific
  order.
- **No live HTTP destination**: the extractor never knows about a specific
  PMS API. Its sole output is the DPMF file.

## Where to read more

- `spec/dpmf-v0.1.md` — the file format.
- `spec/canonical-model-v0.1.md` — the canonical entities.
- `docs/adapter-authoring.md` — how to add a new origin.
- `docs/migration_order.md` — the order in which Gesdén tables are read.
- `docs/schema_map.md` — Gesdén schema reverse-engineering notes.
- `docs/odontograma_decoding.md` — the dental chart bit-mask challenge.
- `docs/windows-deployment.md` — installation on the clinic's Windows host.
