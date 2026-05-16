"""Build SQL Server connections targeting a Gesdén database.

A ``gesden://`` DSN is a thin wrapper around the bits we need to assemble
an ODBC connection string. Two authentication modes are supported:

- SQL Authentication: ``user`` + ``password``.
- Trusted Connection (Windows Auth): no credentials, the OS-level user
  account is presented to SQL Server. Only meaningful when running on
  Windows.

``pyodbc`` is imported lazily so the rest of the package can be installed
and tested on hosts that lack a working ODBC driver manager (notably
macOS dev boxes without ``unixodbc``).
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

ODBC_DRIVER = "ODBC Driver 18 for SQL Server"
_DEFAULT_PORT = 1433

# Direct download URL for ODBC Driver 18 (Microsoft, stable since 2024).
# We surface this in the missing-driver error so operators do not have to
# guess where to find the installer.
_ODBC_DOWNLOAD_URL = (
    "https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
)


class OdbcDriverMissingError(RuntimeError):
    """Raised when the required ODBC driver is not registered on the host."""


def _check_odbc_driver_installed() -> None:
    """Surface a friendly error when ODBC Driver 18 is not registered.

    pyodbc's own error message in this case is the cryptic
    ``IM002 [Microsoft][ODBC Driver Manager] Data source name not found``,
    which routinely sends operators down rabbit holes about DSN files.
    The real cause is almost always that the Microsoft driver has not
    been installed. Catch it early and point at the download page.
    """
    import pyodbc

    available = {d.strip() for d in pyodbc.drivers()}
    if ODBC_DRIVER not in available:
        raise OdbcDriverMissingError(
            f"Required ODBC driver not found on this host: {ODBC_DRIVER!r}.\n"
            f"Installed drivers detected: {sorted(available) or '(none)'}\n"
            f"Install it from: {_ODBC_DOWNLOAD_URL}\n"
            "On Windows pick 'ODBC Driver 18 for SQL Server (x64)'."
        )


@dataclass(slots=True, frozen=True)
class GesdenDsn:
    host: str
    instance: str | None
    port: int
    database: str

    @property
    def server_clause(self) -> str:
        """The SERVER= value: ``host\\instance,port`` or ``host,port``."""
        base = f"{self.host}\\{self.instance}" if self.instance else self.host
        return f"{base},{self.port}"


def parse_dsn(uri: str) -> GesdenDsn:
    """Parse a ``gesden://`` URI.

    Accepted shapes::

        gesden://host/db
        gesden://host:1433/db
        gesden://host\\SQLEXPRESS/db
        gesden://host\\SQLEXPRESS:1433/db

    Backslashes may appear URL-encoded as ``%5C``.
    """
    if not uri.startswith("gesden://"):
        raise ValueError(f"DSN must start with 'gesden://', got {uri!r}")
    parsed = urllib.parse.urlparse(uri)
    if not parsed.path or parsed.path == "/":
        raise ValueError("DSN is missing a /database path component")
    database = parsed.path.lstrip("/")
    netloc = urllib.parse.unquote(parsed.netloc)
    host, instance, port = _split_netloc(netloc)
    return GesdenDsn(host=host, instance=instance, port=port, database=database)


def _split_netloc(netloc: str) -> tuple[str, str | None, int]:
    # netloc shapes covered: host, host:port, host\inst, host\inst:port
    match = re.match(
        r"^(?P<host>[^\\:]+)(?:\\(?P<inst>[^:]+))?(?::(?P<port>\d+))?$",
        netloc,
    )
    if match is None:
        raise ValueError(f"unparseable Gesdén DSN host part: {netloc!r}")
    host = match.group("host")
    instance = match.group("inst")
    port = int(match.group("port")) if match.group("port") else _DEFAULT_PORT
    return host, instance, port


def build_connection_string(
    dsn: GesdenDsn,
    *,
    user: str | None,
    password: str | None,
    trusted_connection: bool,
    trust_server_certificate: bool,
    encrypt: bool = True,
    connect_timeout_seconds: int = 30,
) -> str:
    """Compose an ODBC connection string for ``pyodbc.connect``.

    Either ``trusted_connection=True`` or ``user`` + ``password`` must be
    supplied. Encryption defaults to on; clinics on a private LAN with an
    old SQL Server may need ``trust_server_certificate=True`` because the
    server only presents a self-signed certificate.
    """
    if trusted_connection and (user or password):
        raise ValueError("trusted_connection cannot be combined with user/password")
    if not trusted_connection and (not user or password is None):
        raise ValueError("SQL Authentication requires both user and password")

    parts = [
        f"DRIVER={{{ODBC_DRIVER}}}",
        f"SERVER={dsn.server_clause}",
        f"DATABASE={dsn.database}",
        f"Encrypt={'yes' if encrypt else 'no'}",
        f"TrustServerCertificate={'yes' if trust_server_certificate else 'no'}",
        f"Connection Timeout={connect_timeout_seconds}",
    ]
    if trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        # We don't escape secrets — pyodbc requires the ODBC literal form.
        # The caller is responsible for sourcing the password from a safe place.
        parts.append(f"UID={user}")
        parts.append(f"PWD={password}")
    return ";".join(parts) + ";"


def connect(
    uri: str,
    *,
    user: str | None = None,
    password: str | None = None,
    trusted_connection: bool = False,
    trust_server_certificate: bool = False,
    encrypt: bool = True,
    connect_timeout_seconds: int = 30,
) -> Any:
    """Open a read-only pyodbc connection against a Gesdén database.

    ODBC Driver 18 for SQL Server transcodes SQL_CHAR / VARCHAR columns
    to UTF-8 on the wire by default, even when the source collation is
    ``SQL_Latin1_General_CP1_CI_AS``. The driver does the legwork —
    we instruct pyodbc to interpret the bytes as UTF-8 so that accented
    Spanish characters (ñ, á, é, í, ó, ú, …) round-trip cleanly.

    Earlier revisions of this module set the decoding to ``latin-1`` or
    ``cp1252``; both produced double-decoded mojibake (Ñ rendered as
    ``Ã\\x91``). UTF-8 is now the correct choice for ODBC Driver 18.

    Importers that need to access the raw source bytes can still do so —
    every canonical row carries the unmodified payload under
    ``raw_source_data``.
    """
    import pyodbc

    _check_odbc_driver_installed()
    dsn = parse_dsn(uri)
    conn_str = build_connection_string(
        dsn,
        user=user,
        password=password,
        trusted_connection=trusted_connection,
        trust_server_certificate=trust_server_certificate,
        encrypt=encrypt,
        connect_timeout_seconds=connect_timeout_seconds,
    )
    conn = pyodbc.connect(conn_str, readonly=True, autocommit=True)
    conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-16le")
    return conn
