"""Run a tiny Ω-ECC-T demonstration from the repository root.

Usage:
    python examples/omega_ecc_t_demo.py
"""
from __future__ import annotations

from ecc_tristan import (
    HyperParityGraph,
    LinearBlockCode,
    ReedSolomonErasureCode,
    SparseLDPC,
    bench_hamming74_bsc,
    block_deinterleave,
    block_interleave,
    decode,
    default_oakbench_matrix,
    encode,
    erase_positions,
    min_sum_decode,
)
from ecc_tristan.channels import burst_flip_channel
from ecc_tristan.oak import gate_hamming74
from ecc_tristan.soft_channels import bpsk_awgn_channel, sigma_from_ebn0_db


def main() -> None:
    data = [1, 0, 1, 1]
    codeword = encode(data)
    noisy = burst_flip_channel(codeword, start=2, length=1)
    decoded = decode(noisy.output_bits)
    oak = gate_hamming74(decoded.syndrome, decoded.corrected_position, decoded.oak_trust)

    print("Ω-ECC-T demo")
    print({"data": data, "codeword": codeword, "received": noisy.output_bits})
    print({"decoded": decoded.data_bits, "syndrome": decoded.syndrome, "oak": oak.status, "reason": oak.reason})
    print("bench", bench_hamming74_bsc(trials=32, p=0.03, seed=11).as_dict())

    graph = HyperParityGraph.repetition3()
    print("hyper_parity_graph", graph.nearest_codeword([1, 0, 1]))

    ldpc = SparseLDPC.toy_6_3()
    print("toy_ldpc_hard", ldpc.bit_flip_decode([0, 0, 0, 1, 0, 0]))
    print("toy_ldpc_min_sum", min_sum_decode(ldpc, [5.0, 5.0, 5.0, -1.0, 5.0, 5.0]))

    linear = LinearBlockCode.toy_6_3()
    linear_message = [1, 0, 1]
    linear_codeword = linear.encode(linear_message)
    linear_received = list(linear_codeword)
    linear_received[0] ^= 1
    print("toy_linear_ml", linear.nearest_decode(linear_received))

    rs = ReedSolomonErasureCode(n=10, k=6)
    rs_message = [10, 20, 30, 40, 50, 60]
    rs_codeword = rs.encode(rs_message)
    rs_received = erase_positions(rs_codeword, [0, 3, 5, 9])
    print("reed_solomon_erasure", rs.decode_erasures(rs_received))

    burst_bits = [bit for block in [encode([1, 0, 1, 1]), encode([0, 1, 0, 1])] for bit in block]
    interleaved = block_interleave(burst_bits, depth=2)
    print("interleaver_roundtrip", block_deinterleave(interleaved, depth=2) == burst_bits)

    sigma = sigma_from_ebn0_db(rate=0.5, ebn0_db=3.0)
    soft = bpsk_awgn_channel([0, 1, 0, 1], sigma=sigma, seed=123)
    print("soft_channel_cvcd", soft.reliability_cvcd())

    print("oakbench_matrix")
    for row in default_oakbench_matrix():
        print(row.as_dict())


if __name__ == "__main__":
    main()
