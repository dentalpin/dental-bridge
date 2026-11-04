"""Schema fingerprint tests use metadata rows only."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from dental_bridge.adapters.nemodent.schema_fingerprint import compute_fingerprint


class _Cursor:
    def __init__(self, tables: list[Any], columns: dict[str, list[Any]]) -> None:
        self._tables = tables
        self._columns = columns

    def tables(self, **_kwargs: object) -> _Cursor:
        return self

    def columns(self, *, table: str, column: str) -> _Cursor:
        if table == "STATS_MONTHLY":
            raise UnicodeDecodeError(
                "utf-16-le",
                b"\x00\xd8",
                0,
                2,
                "illegal UTF-16 surrogate",
            )
        self._current = [
            item
            for item in self._columns[table]
            if item.column_name.casefold() == column.casefold()
        ]
        return self

    def fetchall(self) -> list[Any]:
        return self._current if hasattr(self, "_current") else self._tables

    def close(self) -> None:
        pass


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _Cursor:
        return self._cursor


def _table(name: str, table_type: str = "TABLE") -> Any:
    return SimpleNamespace(table_name=name, table_type=table_type)


def _column(
    name: str,
    ordinal: int,
    *,
    data_type: int = 12,
    type_name: str = "TEXT",
    size: int = 50,
    scale: int = 0,
    nullable: int = 1,
) -> Any:
    return SimpleNamespace(
        column_name=name,
        data_type=data_type,
        type_name=type_name,
        column_size=size,
        decimal_digits=scale,
        nullable=nullable,
        ordinal_position=ordinal,
    )


def _fingerprint(tables: list[Any], columns: dict[str, list[Any]]) -> str:
    return compute_fingerprint(_Connection(_Cursor(tables, columns)))  # type: ignore[arg-type]


def test_fingerprint_ignores_views_and_system_tables() -> None:
    tables = [_table("Patient"), _table("MSysObjects"), _table("Patient_Query", "VIEW")]
    columns = {"Patient": [_column("GUID", 1), _column("First", 2)]}

    fingerprint = _fingerprint(tables, columns)

    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == 71


def test_fingerprint_ignores_unrelated_table_with_broken_column_metadata() -> None:
    relevant_only = _fingerprint(
        [_table("Patient")],
        {"Patient": [_column("GUID", 1), _column("First", 2)]},
    )
    with_unrelated_table = _fingerprint(
        [_table("Patient"), _table("STATS_MONTHLY")],
        {"Patient": [_column("GUID", 1), _column("First", 2)]},
    )

    assert with_unrelated_table == relevant_only


def test_fingerprint_is_independent_of_metadata_row_order() -> None:
    first = _fingerprint(
        [_table("Patient"), _table("PERSONNEL")],
        {
            "Patient": [_column("GUID", 1), _column("First", 2)],
            "PERSONNEL": [_column("ID", 1)],
        },
    )
    second = _fingerprint(
        [_table("PERSONNEL"), _table("Patient")],
        {
            "Patient": [_column("First", 2), _column("GUID", 1)],
            "PERSONNEL": [_column("ID", 1)],
        },
    )

    assert first == second


def test_fingerprint_changes_when_column_shape_changes() -> None:
    original = _fingerprint(
        [_table("Patient")],
        {"Patient": [_column("GUID", 1), _column("First", 2, size=20)]},
    )
    changed = _fingerprint(
        [_table("Patient")],
        {"Patient": [_column("GUID", 1), _column("First", 2, size=60)]},
    )

    assert original != changed


def test_fingerprint_rejects_database_without_user_tables() -> None:
    with pytest.raises(ValueError, match="no Nemodent adapter tables"):
        _fingerprint([_table("MSysObjects")], {})
