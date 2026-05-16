"""Read system users from the Gesdén ``TUsers`` table.

Passwords are explicitly excluded — Gesdén stores them in two columns
(``Pass`` and ``Password``) with proprietary hashing. The migration tool
never copies these values; destination PMSs are expected to recreate
accounts and force a password reset via email.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from dental_bridge.adapters.gesden.extractors._rows import iter_dicts

if TYPE_CHECKING:
    import pyodbc


_QUERY = """
SELECT
    u.IdUser,
    u.Login,
    u.Nombre,
    u.Apellidos,
    u.IdCol
FROM TUsers u
ORDER BY u.IdUser
"""


def iter_rows(conn: pyodbc.Connection) -> Iterator[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute(_QUERY)
    return iter_dicts(cursor)
