from ecc_tristan import block_deinterleave, block_interleave, block_interleaver_permutation, default_oakbench_matrix
from ecc_tristan.oakbench_matrix import hamming74_burst_rows, linear_code_ml_bsc_row


def test_block_interleaver_roundtrip_multiple_depths():
    bits = [0, 1, 1, 0, 1, 0, 1, 1, 0]
    for depth in [1, 2, 3, 4, 9]:
        assert block_deinterleave(block_interleave(bits, depth), depth) == bits


def test_block_interleaver_known_permutation():
    assert block_interleaver_permutation(6, depth=2) == [0, 3, 1, 4, 2, 5]


def test_linear_ml_oakbench_row_runs():
    row = linear_code_ml_bsc_row(p=0.0, trials=8, seed=31)
    assert row.code == "toy_6_3_linear_ml"
    assert row.success_rate == 1.0
    assert row.false_accept_rate == 0.0


def test_hamming_burst_interleaver_rows_run():
    rows = hamming74_burst_rows(burst_length=4, blocks=8, interleaver_depth=4)
    assert len(rows) == 2
    assert rows[0].channel == "burst_flip_length"
    assert rows[1].code.endswith("depth_4")
    assert all(0.0 <= row.success_rate <= 1.0 for row in rows)


def test_default_oakbench_matrix_includes_max_improvement_rows():
    rows = default_oakbench_matrix()
    codes = {row.code for row in rows}
    assert "toy_6_3_linear_ml" in codes
    assert "Hamming(7,4)_no_interleaver" in codes
    assert "Hamming(7,4)_block_interleaver_depth_4" in codes
