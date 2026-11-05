"""Shared streaming reader for fixed, allowlisted Access objects."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pyodbc

_BATCH_SIZE = 1000


def iter_rows(
    conn: pyodbc.Connection,
    *,
    table: str,
    columns: Sequence[str],
) -> Iterator[dict[str, Any]]:
    """Yield rows in bounded batches using only adapter-owned identifiers."""
    if not _is_identifier(table) or not columns or not all(_is_identifier(c) for c in columns):
        raise ValueError("unsafe or empty Access table/column allowlist")

    projection = ", ".join(_quote_identifier(column) for column in columns)
    query = f"SELECT {projection} FROM {_quote_identifier(table)}"
    cursor = conn.cursor()
    try:
        cursor.arraysize = _BATCH_SIZE
        cursor.execute(query)
        while batch := cursor.fetchmany(_BATCH_SIZE):
            for row in batch:
                yield dict(zip(columns, row, strict=True))
    finally:
        cursor.close()


def _is_identifier(value: str) -> bool:
    return bool(value) and not any(character in value for character in "[];'\x00")


def _quote_identifier(value: str) -> str:
    return f"[{value.replace(']', ']]')}]"
