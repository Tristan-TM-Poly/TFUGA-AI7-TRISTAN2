from ecc_tristan.gf2 import mat_vec_mul_mod2, nullspace_mod2, rank_mod2, rref_mod2, vec_mat_mul_mod2
from ecc_tristan import LinearBlockCode


def test_gf2_rank_rref_and_nullspace():
    H = [
        [1, 1, 0, 1, 0, 0],
        [0, 1, 1, 0, 1, 0],
        [1, 0, 1, 0, 0, 1],
    ]
    rref, pivots = rref_mod2(H)
    basis = nullspace_mod2(H)
    assert rank_mod2(H) == 3
    assert pivots == [0, 1, 2]
    assert len(basis) == 3
    assert all(mat_vec_mul_mod2(H, vector) == [0, 0, 0] for vector in basis)
    assert len(rref) == 3


def test_vec_matrix_multiplication_mod2():
    G = [
        [1, 1, 1, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [1, 0, 0, 1, 0, 1],
    ]
    assert vec_mat_mul_mod2([1, 0, 1], G) == [0, 1, 1, 1, 0, 1]


def test_linear_block_code_from_parity_checks_encodes_codewords():
    code = LinearBlockCode.toy_6_3()
    assert code.k == 3
    assert code.n == 6
    assert code.rate() == 0.5
    assert code.minimum_distance() == 3
    for message in code.enumerate_messages():
        codeword = code.encode(message)
        assert code.is_codeword(codeword)


def test_linear_block_code_ml_decode_single_error():
    code = LinearBlockCode.toy_6_3()
    message = [1, 0, 1]
    codeword = code.encode(message)
    received = list(codeword)
    received[0] ^= 1
    decoded = code.nearest_decode(received)
    assert decoded.message == message
    assert decoded.codeword == codeword
    assert decoded.distance == 1
    assert decoded.candidates_checked == 8
    assert decoded.status == "nearest_unique"
