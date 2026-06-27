"""Noise channel primitives for Ω-ECC-T.

The functions are deterministic when a seed is supplied. They deliberately use
only the Python standard library so the first OAKBench can run anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import List, Optional, Sequence

Bit = int


def _validate_bits(bits: Sequence[int]) -> List[int]:
    out = [int(b) for b in bits]
    if any(b not in (0, 1) for b in out):
        raise ValueError("bits must contain only 0/1 values")
    return out


@dataclass(frozen=True)
class ChannelReport:
    """A compact CVCD-like summary of a channel realization."""

    input_bits: List[Bit]
    output_bits: List[Bit]
    flipped_positions: List[int]
    erased_positions: List[int]
    channel: str

    @property
    def bit_error_rate(self) -> float:
        if not self.input_bits:
            return 0.0
        errors = sum(a != b for a, b in zip(self.input_bits, self.output_bits))
        return errors / len(self.input_bits)

    def syndrome_hint(self) -> dict:
        """Return a small syndrome-CVCD diagnostic dictionary."""
        return {
            "channel": self.channel,
            "n": len(self.input_bits),
            "flips": len(self.flipped_positions),
            "erasures": len(self.erased_positions),
            "ber": self.bit_error_rate,
            "burst_like": _is_burst_like(self.flipped_positions + self.erased_positions),
        }


def _is_burst_like(positions: Sequence[int]) -> bool:
    if len(positions) < 2:
        return False
    ordered = sorted(set(positions))
    return ordered[-1] - ordered[0] + 1 <= max(3, 2 * len(ordered))


def binary_symmetric_channel(bits: Sequence[int], p: float, seed: Optional[int] = None) -> ChannelReport:
    """Flip each bit independently with probability ``p``."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    rng = random.Random(seed)
    source = _validate_bits(bits)
    out: List[int] = []
    flipped: List[int] = []
    for idx, bit in enumerate(source):
        if rng.random() < p:
            out.append(bit ^ 1)
            flipped.append(idx)
        else:
            out.append(bit)
    return ChannelReport(source, out, flipped, [], "BSC")


def burst_flip_channel(bits: Sequence[int], start: int, length: int) -> ChannelReport:
    """Flip a contiguous burst of bits."""
    source = _validate_bits(bits)
    if length < 0:
        raise ValueError("length must be non-negative")
    out = list(source)
    flipped: List[int] = []
    for idx in range(start, min(start + length, len(out))):
        if idx >= 0:
            out[idx] ^= 1
            flipped.append(idx)
    return ChannelReport(source, out, flipped, [], "burst_flip")


def erasure_channel(bits: Sequence[int], p: float, seed: Optional[int] = None, erasure_value: int = 0) -> ChannelReport:
    """Erase positions with probability ``p`` and replace by ``erasure_value``.

    This keeps a binary output while returning erased positions separately.
    """
    if erasure_value not in (0, 1):
        raise ValueError("erasure_value must be 0 or 1")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    rng = random.Random(seed)
    source = _validate_bits(bits)
    out = list(source)
    erased: List[int] = []
    for idx in range(len(out)):
        if rng.random() < p:
            out[idx] = erasure_value
            erased.append(idx)
    return ChannelReport(source, out, [], erased, "erasure")
