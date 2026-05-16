"""Helpers shared by every extractor module."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pyodbc


def iter_dicts(cursor: pyodbc.Cursor) -> Iterator[dict[str, Any]]:
    """Yield each row of ``cursor`` as a column_name → value dict."""
    columns = [c[0] for c in cursor.description]
    while True:
        batch = cursor.fetchmany(1000)
        if not batch:
            return
        for row in batch:
            yield dict(zip(columns, row, strict=True))
