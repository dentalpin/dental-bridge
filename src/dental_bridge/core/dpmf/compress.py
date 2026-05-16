"""zstd compression helpers for DPMF files.

The container format is plain SQLite at build time. After
:meth:`DpmfWriter.finalise` has computed the integrity hash, the bytes
on disk can be wrapped in a zstd frame, with the resulting file
typically 5-10x smaller for the JSON-heavy payloads we emit.
"""

from __future__ import annotations

from pathlib import Path

import zstandard

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
DEFAULT_LEVEL = 19


def compress_file(source: Path, destination: Path, *, level: int = DEFAULT_LEVEL) -> Path:
    """Read ``source`` and write a zstd-compressed copy to ``destination``."""
    compressor = zstandard.ZstdCompressor(level=level)
    with source.open("rb") as src, destination.open("wb") as dst:
        compressor.copy_stream(src, dst)
    return destination


def decompress_file(source: Path, destination: Path) -> Path:
    """Read a zstd-compressed ``source`` and write the plain bytes to ``destination``."""
    decompressor = zstandard.ZstdDecompressor()
    with source.open("rb") as src, destination.open("wb") as dst:
        decompressor.copy_stream(src, dst)
    return destination


def looks_like_zstd(magic: bytes) -> bool:
    """True if the first four bytes match the zstd frame magic."""
    return magic[:4] == ZSTD_MAGIC
