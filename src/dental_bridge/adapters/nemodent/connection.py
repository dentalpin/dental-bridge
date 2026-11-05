"""Read-only connection to a local Nemodent Access database."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

ACCESS_ODBC_DRIVER = "Microsoft Access Driver (*.mdb, *.accdb)"


class AccessDriverMissingError(RuntimeError):
    """Raised when the 64-bit Access ODBC driver is unavailable."""


class AccessConnectionError(RuntimeError):
    """Raised when an Access database cannot be opened read-only."""


def build_connection_string(path: Path) -> str:
    """Build an ODBC connection string for a local MDB without credentials."""
    source = path.expanduser()
    if source.suffix.lower() != ".mdb":
        raise ValueError("Nemodent source must be an .mdb file")
    if not source.is_file():
        raise FileNotFoundError("Nemodent MDB file does not exist or is not a file")

    resolved = source.resolve(strict=True)
    path_value = str(resolved)
    if any(character in path_value for character in ";{}"):
        raise ValueError("Nemodent MDB path cannot contain ODBC connection delimiters")
    return f"DRIVER={{{ACCESS_ODBC_DRIVER}}};DBQ={path_value};"


def connect(dsn: str | Path, **_kwargs: object) -> Any:
    """Open an MDB through the installed Access ODBC driver in read-only mode.

    ``readonly=True`` sets the ODBC connection access mode; this must be
    validated against the Windows Access driver before production use.
    """
    try:
        pyodbc = importlib.import_module("pyodbc")
    except ImportError as exc:
        raise AccessDriverMissingError(
            "pyodbc is unavailable; reinstall dental-bridge with its locked dependencies"
        ) from exc

    drivers = {driver.strip() for driver in pyodbc.drivers()}
    if ACCESS_ODBC_DRIVER not in drivers:
        raise AccessDriverMissingError(
            f"Required 64-bit ODBC driver not found: {ACCESS_ODBC_DRIVER!r}. "
            f"Installed drivers: {sorted(drivers) or '(none)'}"
        )

    connection_string = build_connection_string(Path(dsn))
    try:
        return pyodbc.connect(connection_string, readonly=True, autocommit=True)
    except Exception as exc:
        raise AccessConnectionError(
            "Could not open Nemodent MDB using the Access ODBC driver in read-only mode"
        ) from exc
