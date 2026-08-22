from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol, Sequence

from .book0 import INVARIANTS
from .models import (
    ArtifactGenome, Candidate, Certificate, GeneratorGenome, Residual,
    VerificationResult, VerificationStatus, stable_hash,
)


@dataclass(frozen=True)
class FrozenBenchmark:
    benchmark_id: str
    baseline_score: float
    minimum_gain: float = 0.0
    max_risk: float = 1.0
    max_complexity: float = 100.0


class Verifier(Protocol):
    verifier_id: str
    def verify(self, candidate: Candidate, benchmark: FrozenBenchmark, residual_before: float) -> VerificationResult: ...


class DefaultVerifier:
    verifier_id = "oak-default-verifier-r0"

    def verify(self, candidate: Candidate, benchmark: FrozenBenchmark, residual_before: float) -> VerificationResult:
        score = candidate.predicted_gain - 0.25 * candidate.persistent_complexity - 0.25 * candidate.compute_cost - candidate.risk - 0.5 * candidate.epistemic_debt
        residual_after = max(0.0, residual_before - max(0.0, score))
        reasons: list[str] = []
        if candidate.risk > benchmark.max_risk:
            reasons.append("risk gate failed")
        if candidate.persistent_complexity > benchmark.max_complexity:
            reasons.append("complexity gate failed")
        if score < benchmark.baseline_score + benchmark.minimum_gain:
            reasons.append("did not beat frozen baseline")
        status = VerificationStatus.PASS if not reasons else VerificationStatus.FAIL
        return VerificationResult(candidate.candidate_id, status, score, residual_after,
                                  (f"benchmark:{benchmark.benchmark_id}", "deterministic-r0-score"),
                                  self.verifier_id, tuple(reasons))


class MetaHMGEngine:
    REPRESENTATIONS = ("hypergraph", "graph", "tensor", "ast", "causal", "state_machine", "hybrid")

    def __init__(self, verifier: Verifier | None = None) -> None:
        self.verifier = verifier or DefaultVerifier()
        self.ledger: list[Certificate] = []
        self.negative_memory: list[dict] = []

    def residualize(self, residuals: Sequence[Residual]) -> float:
        return sum(r.magnitude * (1.0 + r.uncertainty) for r in residuals)

    def generate_candidates(self, genome: GeneratorGenome, residuals: Sequence[Residual]) -> list[Candidate]:
        pressure = self.residualize(residuals)
        reps = self.REPRESENTATIONS[: max(1, min(len(self.REPRESENTATIONS), genome.budget))]
        out: list[Candidate] = []
        for idx, rep in enumerate(reps):
            rep_factor = (1.00, 0.93, 0.87, 0.82, 0.90, 0.78, 1.05)[idx]
            complexity = 1.0 + idx * 0.55
            compute = 0.6 + idx * 0.35
            risk = min(1.0, 0.04 * idx + 0.02 * genome.meta_depth)
            debt = 0.08 * idx
            gain = pressure * rep_factor + len(genome.operators) * 0.6
            payload = {"representation": rep, "objective": genome.objective,
                       "operators": list(genome.operators), "residual_pressure": pressure,
                       "generated": True, "verified": False}
            cid = stable_hash({"generator": genome.id, "payload": payload})[:20]
            out.append(Candidate(cid, genome.id, rep, payload, gain, complexity, compute, risk, debt, False))
        return out

    def tournament(self, candidates: Sequence[Candidate], benchmark: FrozenBenchmark, residual_before: float):
        results = [self.verifier.verify(c, benchmark, residual_before) for c in candidates]
        passing = [(c, r) for c, r in zip(candidates, results) if r.status == VerificationStatus.PASS]
        if not passing:
            self.negative_memory.append({"benchmark": benchmark.benchmark_id, "reason": "no candidate passed"})
            return None, results
        winner, _ = max(passing, key=lambda cr: (cr[1].score, cr[0].utility))
        return winner, results

    def certify(self, input_obj: object, candidate: Candidate, result: VerificationResult, operator: str = "PROMOTE") -> Certificate:
        if result.status != VerificationStatus.PASS:
            raise ValueError("cannot certify an unverified candidate")
        if result.verifier_id == candidate.generator_id:
            raise ValueError("Generator != Judge")
        cert = Certificate(
            stable_hash(input_obj), stable_hash(asdict(candidate)), operator,
            ("R0 deterministic benchmark",),
            ("frozen-baseline", "risk-gate", "complexity-gate", "generator-judge-separation"),
            result.evidence, result.residual_after, 0.1, candidate.risk,
            "discard promoted candidate and return to previous crystal", result.verifier_id,
            metadata={"candidate_id": candidate.candidate_id, "representation": candidate.representation},
        )
        self.ledger.append(cert)
        return cert

    def ablate(self, winner: Candidate, result: VerificationResult, epsilon: float = 0.05) -> dict:
        removable: list[str] = []
        margin = result.score
        for field, cost in (("epistemic_debt", winner.epistemic_debt), ("risk", winner.risk),
                            ("compute_cost", winner.compute_cost * 0.25),
                            ("persistent_complexity", winner.persistent_complexity * 0.25)):
            if cost <= max(epsilon, abs(margin) * 0.1):
                removable.append(field)
        return {"candidate_id": winner.candidate_id, "removable_cost_dimensions": removable, "epsilon": epsilon}

    def distill(self, winner: Candidate, cert: Certificate) -> ArtifactGenome:
        return ArtifactGenome(
            intent=f"regenerate verified {winner.representation} candidate",
            inputs={"receipt_hash": cert.receipt_hash, "candidate_id": winner.candidate_id},
            operators=("REGENERATE", "VERIFY"), constraints=INVARIANTS,
            invariants=("candidate identity", "verifier separation", "provenance hash"),
            evidence_need=(cert.receipt_hash,),
        )

    def regenerate(self, crystal: ArtifactGenome, original: Candidate) -> Candidate:
        if crystal.inputs.get("candidate_id") != original.candidate_id:
            raise ValueError("crystal cannot regenerate a different candidate")
        return original

    def meta_stop(self, verified_gain: float, regenerability_gain: float, transfer_gain: float,
                  optionality_gain: float, complexity: float, risk: float, debt: float, compute: float) -> bool:
        return verified_gain + regenerability_gain + transfer_gain + optionality_gain > complexity + risk + debt + compute
