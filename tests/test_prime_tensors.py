from sage_tristan.prime_tensors import (
    first_primes,
    gap_feature_vector,
    gap_sequence,
    gap_tensor_features,
    is_prime,
    mixed_radix_primorial_coordinates,
    residue_signature_by_index,
    signature_entropy_proxy,
    summarize_prime_sample,
)


def test_is_prime_basic_cases():
    assert not is_prime(1)
    assert is_prime(2)
    assert is_prime(3)
    assert not is_prime(9)
    assert is_prime(29)


def test_first_primes():
    assert first_primes(0) == []
    assert first_primes(6) == [2, 3, 5, 7, 11, 13]


def test_residue_signature_is_nonzero_for_later_prime():
    primes = first_primes(8)
    signature = residue_signature_by_index(primes, 7)
    assert all(value != 0 for value in signature)


def test_gap_sequence_and_features():
    primes = first_primes(6)
    assert gap_sequence(primes) == [1, 2, 2, 4, 2]
    features = gap_feature_vector(4, 7, moduli=(2, 3))
    assert features[:3] == (4.0, 0.0, 1.0)


def test_gap_tensor_features_keys():
    primes = first_primes(6)
    features = gap_tensor_features(primes, max_offset=2, moduli=(2, 3))
    assert (0, 1) in features
    assert (0, 2) in features


def test_mixed_radix_primorial_coordinates():
    assert mixed_radix_primorial_coordinates(17, [2, 3, 5]) == (1, 2, 2)


def test_signature_entropy_proxy():
    assert signature_entropy_proxy([]) == 0.0
    assert signature_entropy_proxy([1, 1, 1]) == 1 / 3
    assert signature_entropy_proxy([1, 2, 3]) == 1.0


def test_prime_tensor_report():
    report = summarize_prime_sample(first_primes(5))
    assert report.prime_count == 5
    assert report.max_prime == 11
    assert report.max_gap == 4
