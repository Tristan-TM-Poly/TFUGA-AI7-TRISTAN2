from __future__ import annotations

import pytest

from omega_prime_value_t.arithmetic import factor_out_twos, jacobi, v2
from omega_prime_value_t.benchmark import deterministic_benchmark
from omega_prime_value_t.campaign import PrimeCampaign, SearchPolicy
from omega_prime_value_t.certificate import build_certificate, verify_certificate
from omega_prime_value_t.families import iter_proth_candidates, proth_number
from omega_prime_value_t.market import score_prime_asset
from omega_prime_value_t.models import CandidateStatus, PrimeCandidate
from omega_prime_value_t.ntt import build_ntt_profile, verify_ntt_profile
from omega_prime_value_t.primality import is_prime, is_probable_prime
from omega_prime_value_t.proth import prove_proth, proth_parameters, verify_proth_proof
from omega_prime_value_t.sieve import primes_up_to, screen_candidate


@pytest.mark.parametrize("value,expected", [(1, 0), (2, 1), (8, 3), (24, 3), (2**31, 31)])
def test_v2(value: int, expected: int) -> None:
    assert v2(value) == expected


def test_factor_out_twos() -> None:
    assert factor_out_twos(15 * 2**27) == (15, 27)


def test_jacobi() -> None:
    assert jacobi(5, 7) == -1
    assert jacobi(2, 15) == 1


@pytest.mark.parametrize("prime", [2, 3, 5, 17, 97, 998244353, 2013265921, 18446744069414584321])
def test_known_primes(prime: int) -> None:
    assert is_prime(prime)


@pytest.mark.parametrize("composite", [0, 1, 4, 9, 21, 341, 561, 1105, 2**64 - 1])
def test_known_composites(composite: int) -> None:
    assert not is_probable_prime(composite)


def test_is_prime_boundary() -> None:
    with pytest.raises(ValueError):
        is_prime(2**64 + 13)


def test_proth_constructor() -> None:
    assert proth_number(119, 23) == 998244353
    with pytest.raises(ValueError):
        proth_number(2, 10)
    with pytest.raises(ValueError):
        proth_number(1025, 10)


def test_iter_proth_candidates_are_odd_k() -> None:
    candidates = list(iter_proth_candidates(8, 2, 9))
    assert [candidate.parameters["k"] for candidate in candidates] == [3, 5, 7, 9]


@pytest.mark.parametrize("prime", [97, 998244353, 2013265921, 18446744069414584321])
def test_proth_proof(prime: int) -> None:
    proof = prove_proth(prime)
    assert proof is not None
    assert verify_proth_proof(proof.to_dict())


def test_non_proth_has_no_proof() -> None:
    assert proth_parameters(101) is None
    assert prove_proth(101) is None


def test_sieve_does_not_misclassify_prime() -> None:
    candidate = PrimeCandidate(3 * 2**8 + 1, "proth", {"k": 3, "n": 8})
    screened = screen_candidate(candidate)
    assert screened.status is CandidateStatus.CANDIDATE
    assert screened.small_factor is None


def test_sieve_composite_factor() -> None:
    candidate = PrimeCandidate(9 * 2**8 + 1, "proth", {"k": 9, "n": 8})
    screened = screen_candidate(candidate)
    assert screened.status is CandidateStatus.FILTERED_COMPOSITE
    assert screened.small_factor in (5, 461)


def test_prime_sieve() -> None:
    assert primes_up_to(20) == [2, 3, 5, 7, 11, 13, 17, 19]


@pytest.mark.parametrize("prime,adicity", [(97, 5), (998244353, 23), (2013265921, 27)])
def test_ntt_profile(prime: int, adicity: int) -> None:
    profile = build_ntt_profile(prime)
    assert profile.two_adicity == adicity
    assert verify_ntt_profile(profile.to_dict())


def test_certificate_round_trip() -> None:
    candidate = PrimeCandidate(
        998244353,
        "proth",
        {"k": 119, "n": 23, "expression": "119*2^23+1"},
        status=CandidateStatus.PROVEN_PRIME,
    )
    proof = prove_proth(candidate.value)
    assert proof is not None
    certificate = build_certificate(
        candidate,
        proof,
        timestamp_utc="2026-08-03T20:00:00+00:00",
        software_commit="fixture",
    )
    valid, errors = verify_certificate(certificate)
    assert valid, errors
    assert certificate.oak["record_claimed"] is False
    assert certificate.verification["ntt_profile"]["two_adicity"] == 23


def test_certificate_tamper_detection() -> None:
    candidate = PrimeCandidate(
        97,
        "proth",
        {"k": 3, "n": 5, "expression": "3*2^5+1"},
        status=CandidateStatus.PROVEN_PRIME,
    )
    proof = prove_proth(97)
    assert proof is not None
    certificate = build_certificate(candidate, proof, timestamp_utc="1970-01-01T00:00:00+00:00")
    payload = certificate.to_dict()
    payload["candidate"]["value"] = 99
    valid, errors = verify_certificate(payload)
    assert not valid
    assert errors


def test_market_score_rewards_verified_ntt() -> None:
    candidate = PrimeCandidate(998244353, "proth", {"k": 119, "n": 23})
    profile = build_ntt_profile(candidate.value)
    rich = score_prime_asset(candidate, ntt_profile=profile, proven=True, independently_verified=True)
    weak = score_prime_asset(candidate, ntt_profile=None, proven=False, independently_verified=False)
    assert rich.total > weak.total
    assert rich.classification.startswith("P")


def test_campaign_produces_certificates_negative_memory_and_hypergraph() -> None:
    report = PrimeCampaign(SearchPolicy(exponent=8, k_min=1, k_max=99, max_results=5)).run()
    assert report.candidates_examined > 0
    assert report.certificates
    assert report.negative_memory
    assert report.hypergraph["nodes"]
    assert report.hypergraph["hyperedges"]
    assert report.hypergraph["claims"]["record_claimed"] is False
    for certificate in report.certificates:
        assert verify_certificate(certificate)[0]


def test_campaign_is_deterministic() -> None:
    policy = SearchPolicy(exponent=8, k_min=1, k_max=99, max_results=5)
    assert PrimeCampaign(policy).run().to_dict() == PrimeCampaign(policy).run().to_dict()


def test_policy_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        PrimeCampaign(SearchPolicy(exponent=4, require_ntt_two_adicity=5))


def test_benchmark_oak_boundaries() -> None:
    payload = deterministic_benchmark()
    assert payload["all_certificates_verified"] is True
    assert payload["certificate_count"] > 0
    assert payload["claims"] == {
        "new_world_record_claimed": False,
        "novel_prime_claimed": False,
        "economic_value_guaranteed": False,
        "cryptographic_secret_generation_claimed": False,
    }
