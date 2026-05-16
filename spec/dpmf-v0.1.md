# DPMF — Dental Practice Migration Format, version 0.1

> **Status: frozen at v0.1.0** as of Sprint 8 of the `dental-bridge`
> reference implementation. Future bug-fix releases of dental-bridge
> may correct typos or clarifications in this document, but the
> on-disk format is now stable. The next breaking change (entity
> addition, layout change, KDF/cipher change) must bump the major
> version to 1.0.

This document describes the on-disk format produced by `dental-bridge`
and consumed by downstream importers. The format is versioned via
[SemVer](https://semver.org/). Breaking changes bump the major version;
additive changes (new optional fields, new entity types) bump the minor.

## Goals

DPMF is designed to be:

- **Single-file portable**: one container, transferable by HTTP upload,
  USB stick, email (if small), or any other mechanism.
- **Inspectable**: every field can be read by any client that speaks SQLite
  and JSON. No proprietary binary encoding.
- **Auditable**: each entity preserves its original source payload alongside
  the canonical representation, so any decoding decision can be reviewed.
- **Versionable**: importers know exactly which spec revision produced the
  file and can refuse incompatible majors.
- **Reproducible**: re-extracting the same source dataset yields the same
  `canonical_uuid` values, so re-imports are idempotent.

## Container

A DPMF file is a SQLite 3 database. The bytes on disk may optionally be
wrapped in two outer layers:

1. **Compression**: zstd, level 19 by default. When applied, the file
   extension SHOULD be `.dpm.zst`. Uncompressed files use `.dpm`.
2. **Encryption**: AES-256-GCM with a key derived from a user-supplied
   passphrase via scrypt (N=2^17, r=8, p=1). When applied, the file
   extension SHOULD be `.dpm.enc` (or `.dpm.zst.enc` for both).

Tools MUST detect the layering by examining the file's magic bytes:

| Bytes (first 4) | Meaning |
|---|---|
| `53 51 4c 69` (`SQLi`) | Raw SQLite — uncompressed, unencrypted |
| `28 b5 2f fd` | zstd frame |
| `44 50 4d 45` (`DPME`) | Encrypted DPMF envelope (custom header) |

The encrypted envelope format is specified in §"Encryption envelope".

## SQLite schema

### `_meta`

Key/value pairs describing the file as a whole.

```sql
CREATE TABLE _meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Required keys:

| Key | Example | Description |
|---|---|---|
| `format_version` | `0.1.0` | DPMF spec SemVer |
| `source_system` | `gesden` | Adapter identifier |
| `source_adapter_version` | `0.0.1` | Version of the adapter that produced the file |
| `source_schema_fingerprint` | `sha256:…` | Hash of the source schema this file came from |
| `exporter_tool` | `dental-bridge` | Name of the producing tool |
| `exporter_version` | `0.1.0` | Version of the producing tool |
| `exported_at` | `2026-05-13T14:23:01Z` | UTC ISO-8601 timestamp |
| `tenant_label` | `clinica-demo` | Human-readable identifier of the originating clinic/tenant |
| `integrity_hash_algo` | `sha256` | Hash algorithm used for the trailer |
| `integrity_hash` | `…hex…` | Hash of the SQLite file bytes excluding this row itself |

### `_entities`

Index of every entity type included in the file.

```sql
CREATE TABLE _entities (
    entity_type    TEXT PRIMARY KEY,
    row_count      INTEGER NOT NULL,
    schema_version TEXT NOT NULL
);
```

`schema_version` is the per-entity SemVer of the canonical model. This lets
us evolve, for example, the `patient` schema in isolation without bumping
the whole format.

### Entity tables

One table per canonical entity type. The column shape is uniform:

```sql
CREATE TABLE <entity_type> (
    canonical_uuid   TEXT PRIMARY KEY,
    source_id        TEXT NOT NULL,
    source_system    TEXT NOT NULL,
    payload          TEXT NOT NULL CHECK (json_valid(payload)),
    raw_source_data  TEXT NOT NULL CHECK (json_valid(raw_source_data)),
    extracted_at     TEXT NOT NULL
);
CREATE INDEX idx_<entity_type>_source ON <entity_type>(source_system, source_id);
```

- `payload` is a JSON serialisation of the canonical Pydantic model
  (`model.model_dump_json()`).
- `raw_source_data` is the original row from the source system, encoded as
  JSON, with all values coerced to JSON-compatible types but no other
  transformation. Importers MAY consult this when the canonical fields are
  insufficient.
- `canonical_uuid` MUST be a UUIDv5 over the concatenation
  `f"{source_system}:{entity_type}:{source_id}"` using the project-wide
  namespace UUID `dde7d63a-1f43-4ed8-8b91-67b5e9c7c0f7`. Including
  `entity_type` in the name guards against collisions when two source
  tables use overlapping primary-key value spaces (integer IDs that
  start from 1 in every table). The value MUST be reproducible across
  re-runs, so importers can rely on it for idempotency.

The canonical entity list for v0.1 is enumerated in `canonical-model-v0.1.md`.

### `_files`

Manifest of every external file referenced by the entities. Binaries
themselves are NEVER embedded — they are transferred separately by a sync
agent that reads this manifest.

```sql
CREATE TABLE _files (
    canonical_uuid          TEXT PRIMARY KEY,
    parent_entity_type      TEXT NOT NULL,
    parent_canonical_uuid   TEXT NOT NULL,
    relative_path           TEXT NOT NULL,
    declared_size_bytes     INTEGER,
    sha256                  TEXT,
    mime_hint               TEXT
);
CREATE INDEX idx_files_parent
    ON _files(parent_entity_type, parent_canonical_uuid);
```

`relative_path` is the path of the file as seen from the clinic-side image
root chosen at extract time, using forward slashes regardless of operating
system. `sha256` SHOULD be populated; it MAY be null when the extractor was
unable to read the binary (file missing, permission denied) — in that case
the importer is expected to surface a warning to the operator.

### `_warnings`

Non-fatal issues observed during extraction. Importers SHOULD propagate
these into their own logs.

```sql
CREATE TABLE _warnings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    source_id   TEXT,
    severity    TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
    code        TEXT NOT NULL,
    message     TEXT NOT NULL,
    raw_data    TEXT CHECK (raw_data IS NULL OR json_valid(raw_data))
);
```

### `PRAGMA user_version`

Set to the format's major version (1 for the 0.x series — yes, "0.x" stays
at `user_version=1` until 1.0). This lets a consumer rule out
incompatibility before doing any further parsing.

## Encryption envelope

When the file is encrypted, the on-disk layout is:

```
+--------+-------------------+-------------------+-----------------------+
| 'DPME' | header_length (u4)| header (JSON utf8)| ciphertext + GCM tag  |
+--------+-------------------+-------------------+-----------------------+
```

`header` is a JSON object with:

```json
{
  "v": 1,
  "kdf": "scrypt",
  "kdf_params": {"n": 131072, "r": 8, "p": 1, "salt": "<base64>"},
  "cipher": "AES-256-GCM",
  "iv": "<base64, 12 bytes>",
  "inner_layout": "zstd" 
}
```

`inner_layout` is `"zstd"` if compression was applied before encryption,
otherwise `"raw"`. After decryption the consumer applies decompression if
indicated, then opens the resulting bytes as a SQLite file.

## Integrity verification

The integrity hash is computed over the *logical content* of the DPMF,
not over the raw SQLite file bytes. SQLite does not guarantee
byte-for-byte stability for a given logical state (page layout depends
on insertion order, rowid choices, vacuum status, etc.), so hashing the
bytes would be brittle. The logical hash is what importers actually
need: "did the payload survive transport unchanged?".

The producer:

1. Computes SHA-256 over a canonical serialisation of:
   - `_entities` rows sorted by `entity_type`.
   - Each entity table's rows sorted by `canonical_uuid`, projecting
     `(canonical_uuid, source_id, source_system, payload, raw_source_data)`.
   - `_files` rows sorted by `canonical_uuid`.
   - `_warnings` rows in insertion order (`id` ASC).
2. The serialisation uses a `|`-separated, newline-terminated line per
   record, prefixed with the source table name. Implementations MUST
   follow the exact format implemented in
   `dental_bridge.core.dpmf.writer.DpmfWriter._compute_logical_hash`
   to remain interoperable.
3. Stores the hex digest in `_meta.integrity_hash`.

The consumer reproduces the procedure and compares the recomputed digest
to the stored value. A mismatch MUST cause the importer to refuse the
file.

## Compatibility policy

- A consumer MUST refuse a file whose `_meta.format_version` major exceeds
  the highest it supports.
- A consumer SHOULD accept files whose minor is greater than its own,
  ignoring entity fields it does not recognise.
- A consumer MUST accept files whose minor is less than or equal to its own.
- Once an entity field is published in a minor release, it MUST NOT be
  removed or have its semantics changed in subsequent minor releases.
  Renames count as a major break.

## Reference test vectors

The `dental-bridge` test suite ships an interoperability fixture under
`tests/unit/test_dpmf_layers.py` that round-trips:

- An uncompressed SQLite DPMF (`SQLi` magic).
- A zstd-compressed DPMF (`28 b5 2f fd` magic).
- An encrypted DPMF (`DPME` magic) with the passphrase
  ``"reference-vector"`` and 1 patient entity.

Implementations that claim DPMF v0.1.0 compatibility MUST pass the
analogous round-trip on their side: producing one file under each
layering and successfully reading it back into the same canonical row
set.

## Conformance levels

A DPMF v0.1.0 implementation MUST support:

- **Reading** raw SQLite, zstd-compressed and DPME-encrypted forms.
- **Producing** at least the raw SQLite form. Producing the compressed
  and encrypted forms is RECOMMENDED but not required (an importer is
  always permitted to ask the operator to decompress/decrypt out-of-band).

## SemVer policy

- **0.1.x → 0.1.y**: bug-fix releases of the *implementation*. The
  format does not change. Importers built for 0.1.0 continue to work.
- **0.1.x → 0.2.0**: minor format additions — new optional fields, new
  entity types. 0.1 importers MUST ignore unknown entity tables and
  fields; 0.2 importers MUST still accept 0.1 files.
- **0.x → 1.0**: breaking change — entity renames, removal of fields,
  changes to the integrity-hash algorithm, changes to the encryption
  envelope. Importers MUST refuse files whose major exceeds the highest
  they support.

## Open questions for v0.2 / v1.0

- DICOM-specific manifest entries (modality, study UID) as optional columns
  in `_files`.
- Per-tenant key wrapping for hosted clinics that want to encrypt with a
  key escrowed by the destination PMS.
- Streaming append: today the entire file is produced in a single run;
  future versions may support incremental updates.
- Odontogram decoding once `docs/odontograma_decoding.md` validation
  against the Gesdén UI is complete.
