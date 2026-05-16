"""Round-trip tests for the DPMF compression and encryption layers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from dental_bridge.core.canonical._enums import Sex
from dental_bridge.core.canonical.base import derive_canonical_uuid
from dental_bridge.core.canonical.patient import CanonicalPatient
from dental_bridge.core.dpmf.compress import compress_file, decompress_file
from dental_bridge.core.dpmf.crypto import decrypt_file, encrypt_file
from dental_bridge.core.dpmf.reader import open_dpmf
from dental_bridge.core.dpmf.writer import DpmfWriter

_TS = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _patient(source_id: str = "1") -> CanonicalPatient:
    return CanonicalPatient(
        canonical_uuid=derive_canonical_uuid("gesden", "patient", source_id),
        source_system="gesden",
        source_id=source_id,
        adapter_version="0.0.1",
        extracted_at=_TS,
        raw_source_data={"IdPac": int(source_id)},
        sex=Sex.UNKNOWN,
    )


def _make_sqlite(tmp_path: Path) -> Path:
    out = tmp_path / "out.dpm"
    with DpmfWriter(
        out,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="test",
    ) as w:
        w.append(_patient("1"))
        w.record_entity_count("patient", 1)
    return out


def test_compress_decompress_roundtrip(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    plain_bytes = plain.read_bytes()
    compressed = tmp_path / "out.dpm.zst"
    compress_file(plain, compressed)
    assert compressed.stat().st_size < plain.stat().st_size
    out = tmp_path / "decompressed.dpm"
    decompress_file(compressed, out)
    assert out.read_bytes() == plain_bytes


def test_encrypt_decrypt_roundtrip(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    plain_bytes = plain.read_bytes()
    encrypted = tmp_path / "out.dpm.enc"
    encrypt_file(plain, encrypted, passphrase="reference-vector", inner_layout="raw")
    out = tmp_path / "decrypted.dpm"
    _, header = decrypt_file(encrypted, out, passphrase="reference-vector")
    assert header.inner_layout == "raw"
    assert out.read_bytes() == plain_bytes


def test_encrypt_wrong_passphrase_fails(tmp_path: Path) -> None:
    from cryptography.exceptions import InvalidTag

    plain = _make_sqlite(tmp_path)
    encrypted = tmp_path / "out.dpm.enc"
    encrypt_file(plain, encrypted, passphrase="correct", inner_layout="raw")
    out = tmp_path / "bogus.dpm"
    with pytest.raises(InvalidTag):
        decrypt_file(encrypted, out, passphrase="WRONG")


def test_reader_handles_plain_sqlite(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    with open_dpmf(plain) as conn:
        assert conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 1


def test_reader_handles_zstd_compressed(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    compressed = tmp_path / "out.dpm.zst"
    compress_file(plain, compressed)
    with open_dpmf(compressed) as conn:
        assert conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 1


def test_reader_handles_encrypted_raw(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    encrypted = tmp_path / "out.dpm.enc"
    encrypt_file(plain, encrypted, passphrase="reference-vector", inner_layout="raw")
    with open_dpmf(encrypted, passphrase="reference-vector") as conn:
        assert conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 1


def test_reader_handles_encrypted_zstd(tmp_path: Path) -> None:
    """Both layers applied: zstd-compressed then encrypted (the recommended flow)."""
    plain = _make_sqlite(tmp_path)
    compressed = tmp_path / "out.dpm.zst"
    compress_file(plain, compressed)
    encrypted = tmp_path / "out.dpm.zst.enc"
    encrypt_file(compressed, encrypted, passphrase="reference-vector", inner_layout="zstd")
    with open_dpmf(encrypted, passphrase="reference-vector") as conn:
        assert conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0] == 1


def test_reader_refuses_encrypted_without_passphrase(tmp_path: Path) -> None:
    plain = _make_sqlite(tmp_path)
    encrypted = tmp_path / "out.dpm.enc"
    encrypt_file(plain, encrypted, passphrase="x", inner_layout="raw")
    with pytest.raises(ValueError, match="passphrase"), open_dpmf(encrypted):
        pass


def test_reader_refuses_unknown_magic(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.dpm"
    bogus.write_bytes(b"GARBAGE" * 100)
    with pytest.raises(ValueError, match="unrecognised"), open_dpmf(bogus):
        pass


def test_zstd_compression_reduces_size_significantly(tmp_path: Path) -> None:
    """Sanity check: zstd level 19 should shrink a JSON-heavy SQLite at least 3x.

    The fixture is tiny so the ratio is modest; on real DPMF files the
    ratio is closer to 5-10x.
    """
    out = tmp_path / "out.dpm"
    with DpmfWriter(
        out,
        source_system="gesden",
        source_adapter_version="0.0.1",
        exporter_version="0.0.1",
        tenant_label="test",
    ) as w:
        for i in range(100):
            w.append(_patient(str(i)))
        w.record_entity_count("patient", 100)
    compressed = tmp_path / "out.dpm.zst"
    compress_file(out, compressed)
    ratio = out.stat().st_size / compressed.stat().st_size
    assert ratio > 2.0, f"compression ratio too low: {ratio:.2f}"
