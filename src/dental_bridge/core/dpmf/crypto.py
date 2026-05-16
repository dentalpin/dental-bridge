"""DPME envelope — AES-256-GCM encryption layer for DPMF files.

On-disk layout:

::

    +--------+-------------------+-------------------+-----------------------+
    | 'DPME' | header_length (u4)| header (JSON utf8)| ciphertext + GCM tag  |
    +--------+-------------------+-------------------+-----------------------+

The header carries the scrypt parameters (cost, block size, parallelism,
salt) and the AES-GCM IV. The key is derived from a user passphrase via
scrypt; the project never persists the key.

``inner_layout`` in the header is ``"zstd"`` if the plaintext was zstd-
compressed before encryption, otherwise ``"raw"``. This makes it possible
to encrypt either an uncompressed SQLite file or a zstd-compressed one
without splitting the format into two variants.
"""

from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

DPME_MAGIC = b"DPME"
_SCRYPT_N = 1 << 17  # 131072
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LEN = 32  # AES-256
_IV_LEN = 12  # 96-bit nonce recommended by NIST for GCM
_SALT_LEN = 16
_HEADER_VERSION = 1


@dataclass(slots=True, frozen=True)
class EnvelopeHeader:
    inner_layout: str  # "raw" or "zstd"
    salt: bytes
    iv: bytes

    def to_json(self) -> bytes:
        import base64

        return json.dumps(
            {
                "v": _HEADER_VERSION,
                "kdf": "scrypt",
                "kdf_params": {
                    "n": _SCRYPT_N,
                    "r": _SCRYPT_R,
                    "p": _SCRYPT_P,
                    "salt": base64.b64encode(self.salt).decode("ascii"),
                },
                "cipher": "AES-256-GCM",
                "iv": base64.b64encode(self.iv).decode("ascii"),
                "inner_layout": self.inner_layout,
            },
            sort_keys=False,
        ).encode("utf-8")

    @classmethod
    def from_json(cls, blob: bytes) -> EnvelopeHeader:
        import base64

        payload = json.loads(blob.decode("utf-8"))
        if payload.get("v") != _HEADER_VERSION:
            raise ValueError(f"unsupported DPME header version: {payload.get('v')!r}")
        if payload.get("cipher") != "AES-256-GCM":
            raise ValueError(f"unsupported cipher: {payload.get('cipher')!r}")
        if payload.get("kdf") != "scrypt":
            raise ValueError(f"unsupported kdf: {payload.get('kdf')!r}")
        return cls(
            inner_layout=payload["inner_layout"],
            salt=base64.b64decode(payload["kdf_params"]["salt"]),
            iv=base64.b64decode(payload["iv"]),
        )


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=_KEY_LEN, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_file(
    plaintext: Path,
    destination: Path,
    *,
    passphrase: str,
    inner_layout: str,
) -> Path:
    """Encrypt ``plaintext`` into a DPME-wrapped ``destination`` file."""
    if inner_layout not in ("raw", "zstd"):
        raise ValueError(f"inner_layout must be 'raw' or 'zstd', got {inner_layout!r}")

    salt = os.urandom(_SALT_LEN)
    iv = os.urandom(_IV_LEN)
    key = _derive_key(passphrase, salt)
    aead = AESGCM(key)

    header = EnvelopeHeader(inner_layout=inner_layout, salt=salt, iv=iv)
    header_blob = header.to_json()

    body = plaintext.read_bytes()
    ciphertext = aead.encrypt(iv, body, header_blob)

    with destination.open("wb") as f:
        f.write(DPME_MAGIC)
        f.write(struct.pack("<I", len(header_blob)))
        f.write(header_blob)
        f.write(ciphertext)
    return destination


def decrypt_file(
    encrypted: Path,
    destination: Path,
    *,
    passphrase: str,
) -> tuple[Path, EnvelopeHeader]:
    """Decrypt a DPME-wrapped file. Returns ``(destination, header)``.

    The destination receives the inner plaintext bytes verbatim — callers
    inspect ``header.inner_layout`` to decide whether further zstd
    decompression is required.
    """
    with encrypted.open("rb") as f:
        magic = f.read(4)
        if magic != DPME_MAGIC:
            raise ValueError("file is not a DPME envelope")
        (header_len,) = struct.unpack("<I", f.read(4))
        header_blob = f.read(header_len)
        header = EnvelopeHeader.from_json(header_blob)
        ciphertext = f.read()

    key = _derive_key(passphrase, header.salt)
    aead = AESGCM(key)
    plaintext = aead.decrypt(header.iv, ciphertext, header_blob)
    destination.write_bytes(plaintext)
    return destination, header


def looks_like_dpme(magic: bytes) -> bool:
    return magic[:4] == DPME_MAGIC
