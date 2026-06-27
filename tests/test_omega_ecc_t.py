from ecc_tristan import HyperParityGraph, bench_hamming74_bsc, decode, encode, syndrome
from ecc_tristan.channels import binary_symmetric_channel, burst_flip_channel
from ecc_tristan.oak import gate_hamming74


def test_hamming74_roundtrip_without_noise():
    data = [1, 0, 1, 1]
    codeword = encode(data)
    result = decode(codeword)
    assert syndrome(codeword) == (0, 0, 0)
    assert result.data_bits == data
    assert result.status == "clean"


def test_hamming74_corrects_single_bit():
    data = [1, 1, 0, 1]
    codeword = encode(data)
    noisy = burst_flip_channel(codeword, start=4, length=1)
    result = decode(noisy.output_bits)
    oak = gate_hamming74(result.syndrome, result.corrected_position, result.oak_trust)
    assert result.data_bits == data
    assert result.corrected_position == 5
    assert oak.accepted


def test_channel_report_has_syndrome_cvcd_hint():
    report = binary_symmetric_channel([0, 1, 1, 0], p=1.0, seed=1)
    hint = report.syndrome_hint()
    assert hint["flips"] == 4
    assert hint["ber"] == 1.0


def test_hyper_parity_graph_repetition3():
    graph = HyperParityGraph.repetition3()
    assert graph.syndrome([1, 1, 1]) == [0, 0]
    decoded = graph.nearest_codeword([1, 0, 1])
    assert decoded.status in {"nearest_unique", "nearest_tie_oak_uncertain"}
    assert decoded.distance == 1


def test_oakbench_runs():
    result = bench_hamming74_bsc(trials=16, p=0.0, seed=3)
    assert result.block_success_rate == 1.0
    assert result.false_accept_rate == 0.0
