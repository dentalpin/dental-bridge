"""Unit tests for the Nemodent Access connection boundary."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from dental_bridge.adapters.nemodent.connection import (
    ACCESS_ODBC_DRIVER,
    AccessConnectionError,
    AccessDriverMissingError,
    build_connection_string,
    connect,
)


def _install_pyodbc(
    monkeypatch: pytest.MonkeyPatch,
    *,
    drivers: list[str],
    connection: object | None = None,
    error: Exception | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_connect(connection_string: str, **kwargs: Any) -> object:
        calls.append((connection_string, kwargs))
        if error is not None:
            raise error
        return connection

    fake = SimpleNamespace(drivers=lambda: drivers, connect=fake_connect)
    monkeypatch.setitem(sys.modules, "pyodbc", fake)
    return calls


def test_builds_connection_string_with_windows_path(tmp_path: Path) -> None:
    mdb = tmp_path / "clinic copy.mdb"
    mdb.write_bytes(b"test fixture")

    connection_string = build_connection_string(mdb)

    assert f"DRIVER={{{ACCESS_ODBC_DRIVER}}}" in connection_string
    assert f"DBQ={mdb.resolve()};" in connection_string
    assert "PWD=" not in connection_string


def test_rejects_odbc_delimiters_in_mdb_path(tmp_path: Path) -> None:
    mdb = tmp_path / "clinic;copy.mdb"
    mdb.write_bytes(b"test fixture")

    with pytest.raises(ValueError, match="ODBC connection delimiters"):
        build_connection_string(mdb)


def test_rejects_non_mdb_source(tmp_path: Path) -> None:
    source = tmp_path / "clinic.csv"
    source.write_text("not an MDB", encoding="utf-8")

    with pytest.raises(ValueError, match=r"\.mdb"):
        build_connection_string(source)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_connection_string(tmp_path / "missing.mdb")


def test_connect_uses_readonly_odbc_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mdb = tmp_path / "clinic.mdb"
    mdb.write_bytes(b"test fixture")
    sentinel = object()
    calls = _install_pyodbc(
        monkeypatch,
        drivers=[ACCESS_ODBC_DRIVER],
        connection=sentinel,
    )

    assert connect(mdb) is sentinel
    assert len(calls) == 1
    _, kwargs = calls[0]
    assert kwargs == {"readonly": True, "autocommit": True}


def test_missing_access_driver_fails_before_connect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mdb = tmp_path / "clinic.mdb"
    mdb.write_bytes(b"test fixture")
    calls = _install_pyodbc(monkeypatch, drivers=["ODBC Driver 18 for SQL Server"])

    with pytest.raises(AccessDriverMissingError, match="64-bit ODBC driver"):
        connect(mdb)
    assert calls == []


def test_connection_error_does_not_expose_driver_details(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mdb = tmp_path / "clinic.mdb"
    mdb.write_bytes(b"test fixture")
    _install_pyodbc(
        monkeypatch,
        drivers=[ACCESS_ODBC_DRIVER],
        error=RuntimeError("private driver diagnostic"),
    )

    with pytest.raises(AccessConnectionError) as exc_info:
        connect(mdb)
    assert "private driver diagnostic" not in str(exc_info.value)
