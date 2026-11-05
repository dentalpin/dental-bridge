"""Optional Windows integration check against an operator-provided sanitized MDB."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from dental_bridge.adapters.nemodent.connection import connect
from dental_bridge.adapters.nemodent.schema_fingerprint import compute_fingerprint


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


@pytest.mark.windows
def test_readonly_connection_does_not_change_sanitized_mdb() -> None:
    raw_path = os.environ.get("NEMODENT_TEST_MDB")
    if not raw_path:
        pytest.skip("set NEMODENT_TEST_MDB to a sanitized test database")

    path = Path(raw_path)
    before = _sha256(path)
    connection = connect(path)
    try:
        assert compute_fingerprint(connection).startswith("sha256:")
    finally:
        connection.close()

    assert _sha256(path) == before
