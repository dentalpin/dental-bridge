"""Force CP1252 decoding for legacy Gesdén string columns.

Gesdén databases collate as ``SQL_Latin1_General_CP1_CI_AS``. Strings come
out of ``pyodbc`` as bytes in CP1252 when SQL_CHAR / SQL_VARCHAR are used.
Applied at connection time via ``setdecoding``; this module provides the
fallback decoder used by tests and by the connection module.
"""

from __future__ import annotations


def decode_cp1252_bytes(value: bytes | str | None) -> str | None:
    """Decode a CP1252-encoded blob; pass strings through unchanged."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.decode("cp1252")
