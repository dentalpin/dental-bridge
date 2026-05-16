#!/usr/bin/env python3
"""Standalone inspector for DPMF files.

Reads a ``.dpm`` container — raw SQLite, zstd-wrapped or DPME-encrypted —
and prints metadata, per-entity row counts and a warnings summary.

Encrypted files require ``--passphrase`` or the
``DENTAL_BRIDGE_DPMF_PASSPHRASE`` environment variable.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a DPMF file.")
    parser.add_argument("path", type=Path, help="Path to the .dpm file")
    parser.add_argument(
        "--passphrase",
        default=os.environ.get("DENTAL_BRIDGE_DPMF_PASSPHRASE"),
        help="Passphrase for encrypted DPMF files (or set DENTAL_BRIDGE_DPMF_PASSPHRASE).",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"file not found: {args.path}", file=sys.stderr)
        return 2

    # Delayed import so the script is still usable without the package
    # installed (printing a hint instead of crashing).
    try:
        from dental_bridge.core.dpmf.reader import open_dpmf
    except ImportError:
        print(
            "dental_bridge is not importable. Run via `uv run python scripts/verify-dpmf.py …`.",
            file=sys.stderr,
        )
        return 1

    with open_dpmf(args.path, passphrase=args.passphrase) as conn:
        meta = dict(conn.execute("SELECT key, value FROM _meta"))
        entities = list(
            conn.execute(
                "SELECT entity_type, row_count, schema_version FROM _entities ORDER BY entity_type"
            )
        )
        warning_rows = conn.execute(
            "SELECT severity, COUNT(*) FROM _warnings GROUP BY severity"
        ).fetchall()
    warnings = dict(warning_rows)

    print(f"DPMF file: {args.path}")
    print(f"  size on disk:             {args.path.stat().st_size:,} bytes")
    print(f"  format_version:           {meta.get('format_version', '?')}")
    print(f"  source_system:            {meta.get('source_system', '?')}")
    print(f"  source_adapter_version:   {meta.get('source_adapter_version', '?')}")
    print(f"  exporter_tool:            {meta.get('exporter_tool', '?')}")
    print(f"  exporter_version:         {meta.get('exporter_version', '?')}")
    print(f"  exported_at:              {meta.get('exported_at', '?')}")
    print(f"  tenant_label:             {meta.get('tenant_label', '?')}")
    print(f"  integrity_hash:           {meta.get('integrity_hash', '?')[:32]}…")
    print()

    print("Entities:")
    for name, count, version in entities:
        print(f"  {name:<32} {count:>10}   (schema {version})")
    print()

    print("Warnings:")
    if not warnings:
        print("  (none)")
    else:
        for severity, count in sorted(warnings.items()):
            print(f"  {severity:<8} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
