from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from .certificate import build_certificate
from .families import iter_proth_candidates
from .hypergraph import build_prime_hypergraph
from .models import CampaignReport, CandidateStatus, PrimeCandidate
from .primality import is_prime
from .proth import prove_proth
from .sieve import screen_candidate


@dataclass(frozen=True, slots=True)
class SearchPolicy:
    exponent: int
    k_min: int = 1
    k_max: int = 999
    sieve_bound: int = 1_000
    max_results: int = 10
    max_value: int = 2**64 - 1
    require_ntt_two_adicity: int = 1

    def validate(self) -> None:
        if self.exponent < 1:
            raise ValueError("exponent must be positive")
        if self.k_min < 1 or self.k_max < self.k_min:
            raise ValueError("invalid k range")
        if self.max_results < 1:
            raise ValueError("max_results must be positive")
        if self.require_ntt_two_adicity > self.exponent:
            raise ValueError("required NTT two-adicity exceeds Proth exponent")


class PrimeCampaign:
    def __init__(self, policy: SearchPolicy):
        policy.validate()
        self.policy = policy

    def run(self) -> CampaignReport:
        report = CampaignReport(policy=asdict(self.policy))
        observed: list[PrimeCandidate] = []
        for candidate in iter_proth_candidates(
            self.policy.exponent,
            self.policy.k_min,
            self.policy.k_max,
            max_value=self.policy.max_value,
        ):
            report.candidates_examined += 1
            screened = screen_candidate(candidate, self.policy.sieve_bound)
            if screened.status is CandidateStatus.FILTERED_COMPOSITE:
                report.filtered_composites += 1
                report.negative_memory.append(
                    {
                        "candidate": str(screened.value),
                        "family": screened.family,
                        "parameters": screened.parameters,
                        "reason": "small_factor",
                        "factor": screened.small_factor,
                        "lesson": "exclude matching modular residue in future shards",
                    }
                )
                observed.append(screened)
                continue
            if screened.value >= 2**64 or not is_prime(screened.value):
                composite = replace(
                    screened,
                    status=CandidateStatus.FILTERED_COMPOSITE,
                    notes=screened.notes + ("deterministic Miller-Rabin composite",),
                )
                report.filtered_composites += 1
                report.negative_memory.append(
                    {
                        "candidate": str(composite.value),
                        "family": composite.family,
                        "parameters": composite.parameters,
                        "reason": "miller_rabin_composite",
                        "factor": None,
                        "lesson": "retain as non-factorized composite evidence",
                    }
                )
                observed.append(composite)
                continue
            probable = replace(screened, status=CandidateStatus.PROBABLE_PRIME)
            report.probable_primes += 1
            proof = prove_proth(probable.value)
            if proof is None:
                observed.append(probable)
                continue
            proven = replace(probable, status=CandidateStatus.PROVEN_PRIME, witness=proof.witness)
            report.proven_primes += 1
            observed.append(proven)
            report.certificates.append(
                build_certificate(
                    proven,
                    proof,
                    timestamp_utc="1970-01-01T00:00:00+00:00",
                    software_commit="deterministic-fixture",
                )
            )
            if len(report.certificates) >= self.policy.max_results:
                break
        report.hypergraph = build_prime_hypergraph(observed, report.certificates)
        return report
