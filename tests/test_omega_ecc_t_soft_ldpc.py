from ecc_tristan import SparseLDPC, hard_bits_from_llr, min_sum_decode
from ecc_tristan.oakbench_matrix import toy_ldpc_awgn_min_sum_row


def test_llr_hard_decision_convention():
    assert hard_bits_from_llr([2.0, 0.0, -0.1, -5.0]) == [0, 0, 1, 1]


def test_soft_decoder_accepts_clear_zero_codeword():
    code = SparseLDPC.toy_6_3()
    result = min_sum_decode(code, [5.0] * code.n)
    assert result.converged
    assert result.status == "converged_initial"
    assert result.decoded == [0] * code.n


def test_soft_decoder_repairs_one_low_confidence_symbol():
    code = SparseLDPC.toy_6_3()
    llr = [5.0] * code.n
    llr[3] = -1.0
    result = min_sum_decode(code, llr, max_iterations=10, normalize=1.0)
    assert result.converged
    assert result.decoded == [0] * code.n
    assert result.iterations >= 1
    assert result.weak_positions


def test_awgn_oakbench_row_runs():
    row = toy_ldpc_awgn_min_sum_row(ebn0_db=3.0, trials=8, seed=23)
    assert row.code == "toy_6_3_ldpc_min_sum"
    assert row.channel == "BPSK_AWGN_EbN0_dB"
    assert 0.0 <= row.success_rate <= 1.0
    assert 0.0 <= row.residual_rate <= 1.0
    assert 0.0 <= row.false_accept_rate <= 1.0
