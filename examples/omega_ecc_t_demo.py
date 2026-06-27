"""Run a tiny Ω-ECC-T demonstration from the repository root.

Usage:
    python examples/omega_ecc_t_demo.py
"""
from __future__ import annotations

from ecc_tristan import HyperParityGraph, SparseLDPC, bench_hamming74_bsc, decode, default_oakbench_matrix, encode
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
    print("toy_ldpc", ldpc.bit_flip_decode([0, 0, 0, 1, 0, 0]))

    sigma = sigma_from_ebn0_db(rate=0.5, ebn0_db=3.0)
    soft = bpsk_awgn_channel([0, 1, 0, 1], sigma=sigma, seed=123)
    print("soft_channel_cvcd", soft.reliability_cvcd())

    print("oakbench_matrix")
    for row in default_oakbench_matrix():
        print(row.as_dict())


if __name__ == "__main__":
    main()
