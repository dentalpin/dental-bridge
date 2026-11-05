"""Streaming Access table reader tests."""

from __future__ import annotations

from typing import ClassVar

import pytest

from dental_bridge.adapters.nemodent.extractors._rows import iter_rows


class _Cursor:
    description: ClassVar[list[tuple[str]]] = [("GUID",), ("Name",)]

    def __init__(self) -> None:
        self.query: str | None = None
        self.closed = False
        self._batches = [[("g-1", "A"), ("g-2", "B")], []]

    def execute(self, query: str) -> _Cursor:
        self.query = query
        return self

    def fetchmany(self, _size: int) -> list[tuple[str, str]]:
        return self._batches.pop(0)

    def close(self) -> None:
        self.closed = True


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _Cursor:
        return self._cursor


def test_iter_rows_projects_allowlisted_columns_and_closes_cursor() -> None:
    cursor = _Cursor()
    rows = list(iter_rows(_Connection(cursor), table="Patient", columns=("GUID", "Name")))  # type: ignore[arg-type]

    assert rows == [{"GUID": "g-1", "Name": "A"}, {"GUID": "g-2", "Name": "B"}]
    assert cursor.query == "SELECT [GUID], [Name] FROM [Patient]"
    assert cursor.closed


@pytest.mark.parametrize(
    ("table", "columns"),
    [
        ("Patient; DROP TABLE", ("GUID",)),
        ("Patient", ()),
        ("Patient", ("GUID] FROM OTHER",)),
    ],
)
def test_iter_rows_rejects_untrusted_identifiers(table: str, columns: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="allowlist"):
        list(iter_rows(_Connection(_Cursor()), table=table, columns=columns))  # type: ignore[arg-type]
