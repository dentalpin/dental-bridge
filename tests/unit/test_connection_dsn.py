"""Tests for the Gesdén DSN parser and connection-string builder.

We do not actually open a connection here — that requires a real SQL
Server. We only verify the URI parsing and the connection-string
assembly.
"""

from __future__ import annotations

import pytest

from dental_bridge.adapters.gesden.connection import (
    build_connection_string,
    parse_dsn,
)


def test_parses_host_only_dsn() -> None:
    dsn = parse_dsn("gesden://server/SOURCE_DB")
    assert dsn.host == "server"
    assert dsn.instance is None
    assert dsn.port == 1433
    assert dsn.database == "SOURCE_DB"
    assert dsn.server_clause == "server,1433"


def test_parses_named_instance() -> None:
    dsn = parse_dsn("gesden://server%5CSQLEXPRESS/db")
    assert dsn.host == "server"
    assert dsn.instance == "SQLEXPRESS"
    assert dsn.server_clause == "server\\SQLEXPRESS,1433"


def test_parses_custom_port() -> None:
    dsn = parse_dsn("gesden://server:1450/db")
    assert dsn.port == 1450
    assert dsn.server_clause == "server,1450"


def test_parses_instance_and_port() -> None:
    dsn = parse_dsn("gesden://srv%5CSQLEXPRESS:1450/db")
    assert dsn.instance == "SQLEXPRESS"
    assert dsn.port == 1450


def test_rejects_missing_database() -> None:
    with pytest.raises(ValueError):
        parse_dsn("gesden://server")


def test_rejects_wrong_scheme() -> None:
    with pytest.raises(ValueError):
        parse_dsn("mssql://server/db")


def test_build_conn_string_sql_auth() -> None:
    dsn = parse_dsn("gesden://h/db")
    s = build_connection_string(
        dsn,
        user="sa",
        password="P@ss",
        trusted_connection=False,
        trust_server_certificate=True,
    )
    assert "DRIVER={ODBC Driver 18 for SQL Server}" in s
    assert "SERVER=h,1433" in s
    assert "DATABASE=db" in s
    assert "UID=sa" in s
    assert "PWD=P@ss" in s
    assert "TrustServerCertificate=yes" in s
    assert "Trusted_Connection" not in s


def test_build_conn_string_windows_auth() -> None:
    dsn = parse_dsn("gesden://h/db")
    s = build_connection_string(
        dsn,
        user=None,
        password=None,
        trusted_connection=True,
        trust_server_certificate=False,
    )
    assert "Trusted_Connection=yes" in s
    assert "UID=" not in s
    assert "PWD=" not in s


def test_build_conn_string_refuses_mixed_auth() -> None:
    dsn = parse_dsn("gesden://h/db")
    with pytest.raises(ValueError):
        build_connection_string(
            dsn,
            user="sa",
            password="x",
            trusted_connection=True,
            trust_server_certificate=False,
        )


def test_build_conn_string_requires_credentials_when_not_trusted() -> None:
    dsn = parse_dsn("gesden://h/db")
    with pytest.raises(ValueError):
        build_connection_string(
            dsn,
            user=None,
            password=None,
            trusted_connection=False,
            trust_server_certificate=False,
        )
