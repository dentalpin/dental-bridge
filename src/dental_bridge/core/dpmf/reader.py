"""Read DPMF files regardless of which optional layers wrap the SQLite.

The reader inspects the first four bytes to decide how to peel the file:

- ``SQLi`` (53 51 4c 69) — raw SQLite, opened directly.
- ``28 b5 2f fd``       — zstd frame, decompressed to a temp SQLite.
- ``DPME``              — DPME envelope, decrypted (optionally
                          decompressed) to a temp SQLite.

The returned object is a context manager that yields a
``sqlite3.Connection`` opened read-only on the inner SQLite. The temp
file is removed on exit.
"""

from __future__ import annotations

import contextlib
import sqlite3
import tempfile
from collections.abc import Iterator
from pathlib import Path

from dental_bridge.core.dpmf.compress import (
    ZSTD_MAGIC,
    decompress_file,
    looks_like_zstd,
)
from dental_bridge.core.dpmf.crypto import (
    DPME_MAGIC,
    decrypt_file,
    looks_like_dpme,
)

_SQLITE_MAGIC = b"SQLi"


@contextlib.contextmanager
def open_dpmf(
    path: Path,
    *,
    passphrase: str | None = None,
) -> Iterator[sqlite3.Connection]:
    """Yield a read-only ``sqlite3.Connection`` over the inner SQLite.

    Raises ``ValueError`` if the file is encrypted and no passphrase was
    supplied, or if the passphrase fails to decrypt.
    """
    with path.open("rb") as f:
        magic = f.read(4)

    if magic[:4] == _SQLITE_MAGIC:
        # Already a plain SQLite — open directly.
        yield from _open_readonly(path)
        return

    tmpdir = Path(tempfile.mkdtemp(prefix="dpmf-"))
    try:
        if looks_like_dpme(magic):
            if not passphrase:
                raise ValueError("encrypted DPMF file requires a passphrase")
            inner = tmpdir / "inner.bin"
            _, header = decrypt_file(path, inner, passphrase=passphrase)
            if header.inner_layout == "zstd":
                sqlite_path = tmpdir / "sqlite.dpm"
                decompress_file(inner, sqlite_path)
            else:
                sqlite_path = inner
        elif looks_like_zstd(magic):
            sqlite_path = tmpdir / "sqlite.dpm"
            decompress_file(path, sqlite_path)
        else:
            raise ValueError(
                f"unrecognised DPMF magic bytes: {magic.hex()} — expected "
                f"SQLite ({_SQLITE_MAGIC.hex()}), zstd ({ZSTD_MAGIC.hex()}) "
                f"or DPME ({DPME_MAGIC.hex()})"
            )
        yield from _open_readonly(sqlite_path)
    finally:
        for child in tmpdir.glob("*"):
            child.unlink(missing_ok=True)
        tmpdir.rmdir()


def _open_readonly(path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        yield conn
    finally:
        conn.close()
