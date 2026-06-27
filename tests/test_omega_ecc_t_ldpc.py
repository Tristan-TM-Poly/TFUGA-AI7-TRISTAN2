from ecc_tristan import SparseLDPC, default_oakbench_matrix
from ecc_tristan.channels import burst_flip_channel
from ecc_tristan.soft_channels import bpsk_awgn_channel, sigma_from_ebn0_db


def test_toy_ldpc_accepts_zero_codeword():
    code = SparseLDPC.toy_6_3()
    assert code.is_codeword([0, 0, 0, 0, 0, 0])
    assert code.syndrome([1, 0, 0, 0, 0, 0]) == [1, 0, 1]


def test_toy_ldpc_bit_flip_corrects_single_error():
    code = SparseLDPC.toy_6_3()
    source = [0, 0, 0, 0, 0, 0]
    noisy = burst_flip_channel(source, start=3, length=1)
    decoded = code.bit_flip_decode(noisy.output_bits, max_iterations=10)
    assert decoded.converged
    assert decoded.decoded == source


def test_soft_awgn_llr_and_hard_bits_are_deterministic():
    sigma = sigma_from_ebn0_db(rate=0.5, ebn0_db=3.0)
    report = bpsk_awgn_channel([0, 1, 0, 1], sigma=sigma, seed=123)
    assert report.hard_bits() == [0, 1, 0, 1]
    assert report.reliability_cvcd()["channel"] == "BPSK_AWGN"


def test_default_oakbench_matrix_runs():
    rows = default_oakbench_matrix()
    assert len(rows) >= 5
    assert all(0.0 <= row.success_rate <= 1.0 for row in rows)
