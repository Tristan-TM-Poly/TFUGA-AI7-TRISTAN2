from ecc_tristan import ReedSolomonErasureCode, erase_positions, default_oakbench_matrix
from ecc_tristan.oakbench_matrix import reed_solomon_erasure_row
from ecc_tristan.reed_solomon import gf_div, gf_inv, gf_mul, lagrange_interpolate, poly_eval


def test_gf256_basic_arithmetic_identities():
    for value in [1, 2, 3, 5, 17, 29, 255]:
        assert gf_mul(value, 1) == value
        assert gf_mul(value, gf_inv(value)) == 1
        assert gf_div(value, value) == 1
    assert gf_mul(0, 123) == 0


def test_lagrange_interpolation_recovers_polynomial_coefficients():
    coefficients = [7, 11, 19, 23]
    points = [(x, poly_eval(coefficients, x)) for x in [1, 2, 3, 4]]
    assert lagrange_interpolate(points, degree_limit=4) == coefficients


def test_reed_solomon_erasure_recovery_at_capacity():
    code = ReedSolomonErasureCode(n=10, k=6)
    message = [10, 20, 30, 40, 50, 60]
    codeword = code.encode(message)
    received = erase_positions(codeword, [0, 3, 5, 9])
    decoded = code.decode_erasures(received)
    assert decoded.recovered
    assert decoded.message == message
    assert decoded.codeword == codeword
    assert decoded.known_symbols == 6
    assert decoded.oak_trust == 1.0


def test_reed_solomon_rejects_too_many_erasures():
    code = ReedSolomonErasureCode(n=10, k=6)
    message = [1, 2, 3, 4, 5, 6]
    received = erase_positions(code.encode(message), [0, 1, 2, 3, 4])
    decoded = code.decode_erasures(received)
    assert not decoded.recovered
    assert decoded.status == "insufficient_known_symbols"
    assert decoded.message is None
    assert decoded.oak_trust == 0.0


def test_reed_solomon_rejects_inconsistent_known_symbol():
    code = ReedSolomonErasureCode(n=10, k=6)
    message = [1, 3, 5, 7, 9, 11]
    codeword = code.encode(message)
    received = erase_positions(codeword, [2, 4])
    received[8] ^= 1
    decoded = code.decode_erasures(received)
    assert not decoded.recovered
    assert decoded.status == "inconsistent_known_symbols_oak_reject"
    assert decoded.oak_trust == 0.0


def test_reed_solomon_oakbench_row_and_default_matrix():
    row = reed_solomon_erasure_row(erasures=4, trials=8)
    assert row.code == "RS(10,6)_GF256_erasure"
    assert row.success_rate == 1.0
    assert row.false_accept_rate == 0.0
    codes = {item.code for item in default_oakbench_matrix()}
    assert "RS(10,6)_GF256_erasure" in codes
