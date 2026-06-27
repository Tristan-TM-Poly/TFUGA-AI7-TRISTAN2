"""OAKBench matrix helpers for comparing Ω-ECC-T baselines."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List

from .benchmarks import bench_hamming74_bsc
from .channels import binary_symmetric_channel
from .ldpc import SparseLDPC
from .minsum import min_sum_decode
from .soft_channels import bpsk_awgn_channel, sigma_from_ebn0_db


@dataclass(frozen=True)
class MatrixRow:
    code: str
    channel: str
    parameter: float
    trials: int
    success_rate: float
    residual_rate: float
    false_accept_rate: float

    def as_dict(self) -> dict:
        return asdict(self)


def hamming_bsc_rows(probabilities: Iterable[float], trials: int = 64, seed: int = 7) -> List[MatrixRow]:
    rows: List[MatrixRow] = []
    for idx, p in enumerate(probabilities):
        result = bench_hamming74_bsc(trials=trials, p=p, seed=seed + 1000 * idx)
        rows.append(
            MatrixRow(
                code="Hamming(7,4)",
                channel="BSC",
                parameter=p,
                trials=trials,
                success_rate=result.block_success_rate,
                residual_rate=1.0 - result.oak_accept_rate,
                false_accept_rate=result.false_accept_rate,
            )
        )
    return rows


def toy_ldpc_bsc_row(p: float = 0.02, trials: int = 64, seed: int = 13) -> MatrixRow:
    """Benchmark the toy LDPC on BSC using the all-zero codeword.

    This is not a full communications benchmark because the tiny toy code does
    not yet include a generator matrix. It tests decoder convergence and OAK
    residual rate against channel corruptions.
    """
    code = SparseLDPC.toy_6_3()
    source = [0] * code.n
    successes = 0
    residuals = 0
    false_accepts = 0
    for i in range(trials):
        report = binary_symmetric_channel(source, p=p, seed=seed + i)
        decoded = code.bit_flip_decode(report.output_bits)
        if decoded.converged:
            if decoded.decoded == source:
                successes += 1
            else:
                false_accepts += 1
        else:
            residuals += 1
    accepts = trials - residuals
    return MatrixRow(
        code="toy_6_3_ldpc_bit_flip",
        channel="BSC",
        parameter=p,
        trials=trials,
        success_rate=successes / trials,
        residual_rate=residuals / trials,
        false_accept_rate=false_accepts / max(1, accepts),
    )


def toy_ldpc_awgn_min_sum_row(ebn0_db: float = 3.0, trials: int = 64, seed: int = 23) -> MatrixRow:
    """Benchmark toy LDPC soft min-sum decoding on BPSK/AWGN.

    The tiny code uses the all-zero codeword only; this measures decoder
    convergence and OAK accounting, not a full production communication stack.
    """
    code = SparseLDPC.toy_6_3()
    source = [0] * code.n
    # The toy_6_3 scaffold has roughly rate 1/2: 3 constraints over 6 bits.
    sigma = sigma_from_ebn0_db(rate=0.5, ebn0_db=ebn0_db)
    successes = 0
    residuals = 0
    false_accepts = 0
    for i in range(trials):
        report = bpsk_awgn_channel(source, sigma=sigma, seed=seed + i)
        decoded = min_sum_decode(code, report.llr, max_iterations=20, normalize=0.9)
        if decoded.converged:
            if decoded.decoded == source:
                successes += 1
            else:
                false_accepts += 1
        else:
            residuals += 1
    accepts = trials - residuals
    return MatrixRow(
        code="toy_6_3_ldpc_min_sum",
        channel="BPSK_AWGN_EbN0_dB",
        parameter=ebn0_db,
        trials=trials,
        success_rate=successes / trials,
        residual_rate=residuals / trials,
        false_accept_rate=false_accepts / max(1, accepts),
    )


def default_oakbench_matrix() -> List[MatrixRow]:
    return hamming_bsc_rows([0.0, 0.01, 0.05, 0.10], trials=64, seed=7) + [
        toy_ldpc_bsc_row(p=0.02, trials=64, seed=13),
        toy_ldpc_awgn_min_sum_row(ebn0_db=3.0, trials=64, seed=23),
    ]
