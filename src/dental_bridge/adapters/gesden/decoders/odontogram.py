"""Decode Gesdén's ``PiezasAdu`` / ``PiezasLec`` tooth bit-masks to FDI.

Gesdén stores the affected adult teeth of a treatment as a 32-bit
``PiezasAdu`` field (and the deciduous teeth as ``PiezasLec``). Each
bit position corresponds to a single tooth in a fixed quadrant order.
The mapping isn't documented officially; it was reverse-engineered by
ranking bit frequencies for ``IdTipoOdg=24`` (implants) in
``SOURCE_DB`` against the known clinical reality that implants
overwhelmingly target first molars (FDI 16, 26, 36, 46).

Empirical alignment:

| Bit | Frequency | Implied FDI | Tooth                     |
|----:|----------:|------------:|---------------------------|
|   2 |       755 |          16 | upper-right 1st molar     |
|  13 |       753 |          26 | upper-left  1st molar     |
|  18 |       603 |          46 | lower-right 1st molar     |
|  29 |       526 |          36 | lower-left  1st molar     |

A natural quadrant order falls out:

| Bits   | Quadrant            | FDI range  | Formula              |
|--------|---------------------|------------|----------------------|
|  0– 7  | upper-right (1)     | 18→11      | ``18 - bit``         |
|  8–15  | upper-left  (2)     | 21→28      | ``13 + bit``         |
| 16–23  | lower-right (4)     | 48→41      | ``64 - bit``         |
| 24–31  | lower-left  (3)     | 31→38      | ``7 + bit``          |

``PiezasLec`` follows the same shape but indexes the deciduous
quadrants 5/6/8/7 — the source database barely uses it (mostly
zero), so the decoder is implemented but not yet field-validated.

Surface decoding (``ZonasPieza`` bit-mask) is intentionally **not**
attempted here: the encoding remains uncertain (see
``docs/odontograma_decoding.md``) and a wrong surface would silently
corrupt the destination odontogram. Importers should consume
``teeth`` and treat ``surfaces`` as ``None``.
"""

from __future__ import annotations


def _bits_set(value: int) -> list[int]:
    """Return the positions of all set bits in ``value`` (0-indexed, low → high)."""
    positions: list[int] = []
    bit = 0
    remaining = value
    while remaining > 0:
        if remaining & 1:
            positions.append(bit)
        remaining >>= 1
        bit += 1
    return positions


def _adult_fdi_for_bit(bit: int) -> int | None:
    """Return the adult FDI tooth number for a ``PiezasAdu`` bit position, or None."""
    if 0 <= bit <= 7:
        return 18 - bit
    if 8 <= bit <= 15:
        return 13 + bit  # 21..28
    if 16 <= bit <= 23:
        return 64 - bit  # 48..41
    if 24 <= bit <= 31:
        return 7 + bit  # 31..38
    return None


def _deciduous_fdi_for_bit(bit: int) -> int | None:
    """Return the deciduous FDI tooth for a ``PiezasLec`` bit position, or None.

    Deciduous quadrants are 5 (UR), 6 (UL), 7 (LL), 8 (LR). Five teeth
    per quadrant (e to a → 1 to 5). The bit order mirrors the adult
    quadrant pattern: UR first (bits 0–4), UL (5–9), LR (10–14),
    LL (15–19).
    """
    if 0 <= bit <= 4:
        return 55 - bit  # 55..51
    if 5 <= bit <= 9:
        return 56 + bit  # 61..65
    if 10 <= bit <= 14:
        return 95 - bit  # 85..81
    if 15 <= bit <= 19:
        return 56 + bit  # 71..75
    return None


def decode_piezas_adu(value: object | None) -> list[int]:
    """Return the adult FDI tooth numbers encoded in a ``PiezasAdu`` value.

    Accepts the raw Gesdén ``numeric`` column. Returns an empty list
    when the value is null, zero, unparseable, or every bit is out of
    the adult range.
    """
    if value in (None, "", 0):
        return []
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        return []
    if ivalue <= 0:
        return []
    teeth: list[int] = []
    for bit in _bits_set(ivalue):
        fdi = _adult_fdi_for_bit(bit)
        if fdi is not None:
            teeth.append(fdi)
    return teeth


def decode_piezas_lec(value: object | None) -> list[int]:
    """Return the deciduous FDI tooth numbers encoded in a ``PiezasLec`` value.

    The Gesdén UI validation pass is still pending for the deciduous
    mapping — the decoder is exposed for completeness but its output
    should be treated as best-effort until field-checked.
    """
    if value in (None, "", 0):
        return []
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        return []
    if ivalue <= 0:
        return []
    teeth: list[int] = []
    for bit in _bits_set(ivalue):
        fdi = _deciduous_fdi_for_bit(bit)
        if fdi is not None:
            teeth.append(fdi)
    return teeth
