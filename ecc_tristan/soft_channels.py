"""Soft channel primitives for future BayesDecoder_T / min-sum LDPC work."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class SoftChannelReport:
    input_bits: List[int]
    symbols: List[float]
    llr: List[float]
    sigma: float
    channel: str

    def hard_bits(self) -> List[int]:
        """Map positive LLR to 0 and negative LLR to 1."""
        return [0 if value >= 0 else 1 for value in self.llr]

    def reliability_cvcd(self) -> dict:
        magnitudes = [abs(x) for x in self.llr]
        if not magnitudes:
            return {"channel": self.channel, "n": 0, "mean_abs_llr": 0.0, "weak_positions": []}
        mean_abs = sum(magnitudes) / len(magnitudes)
        weak = [idx for idx, value in enumerate(magnitudes) if value < mean_abs * 0.5]
        return {
            "channel": self.channel,
            "n": len(magnitudes),
            "sigma": self.sigma,
            "mean_abs_llr": mean_abs,
            "weak_positions": weak,
        }


def bpsk_awgn_channel(bits: Sequence[int], sigma: float, seed: Optional[int] = None) -> SoftChannelReport:
    """Transmit bits through BPSK + AWGN and return log-likelihood ratios.

    Convention: bit 0 -> +1, bit 1 -> -1. For AWGN with variance sigma²,
    LLR = 2*y/sigma².
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    source = [int(x) for x in bits]
    if any(x not in (0, 1) for x in source):
        raise ValueError("bits must be binary")
    rng = random.Random(seed)
    symbols: List[float] = []
    llr: List[float] = []
    variance = sigma * sigma
    for bit in source:
        clean = 1.0 if bit == 0 else -1.0
        y = clean + rng.gauss(0.0, sigma)
        symbols.append(y)
        llr.append(2.0 * y / variance)
    return SoftChannelReport(source, symbols, llr, sigma, "BPSK_AWGN")


def sigma_from_ebn0_db(rate: float, ebn0_db: float) -> float:
    """Return BPSK AWGN sigma from code rate and Eb/N0 in dB."""
    if rate <= 0:
        raise ValueError("rate must be positive")
    ebn0 = 10 ** (ebn0_db / 10.0)
    return math.sqrt(1.0 / (2.0 * rate * ebn0))
