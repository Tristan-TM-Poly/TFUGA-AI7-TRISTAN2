from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, Mapping, Sequence

from .ledger import EpistemicLedger, NegativeMemory
from .models import (
    ClaimRecord,
    Diagnosis,
    FailureKind,
    FrontierKind,
    RepresentationCandidate,
    StrategyPath,
    TruthLevel,
)


class MetaGTNTEngine:
    """Small deterministic core for Ω-META-GTNT-T∞².

    The engine is deliberately conservative: it classifies operational failure
    signals, compares representations and strategy paths, prunes known-dead
    paths, and enforces explicit recursion/promotion gates. It does not infer
    mathematical independence, undecidability, or truth from heuristic signals.
    """

    REPRESENTATION_WEIGHTS = {
        "sparsity": 1.0,
        "verifiability": 1.5,
        "invariant_retention": 1.5,
        "dimension_cost": 0.5,
        "compute_cost": 0.8,
        "reconstruction_error": 2.0,
    }

    def __init__(self, negative_memory: NegativeMemory | None = None) -> None:
        self.negative_memory = negative_memory or NegativeMemory()

    @staticmethod
    def diagnose_failure(signals: Mapping[str, bool | float | int]) -> Diagnosis:
        r: list[str] = []

        if bool(signals.get("contradiction_detected")):
            return Diagnosis(FrontierKind.LOGICAL, FailureKind.CONTRADICTION, 1.0,
                             ("explicit contradiction signal",))
        if bool(signals.get("formal_independence_proved")):
            return Diagnosis(FrontierKind.LOGICAL, FailureKind.AXIOM_INSUFFICIENT, 1.0,
                             ("formal independence certificate supplied",))
        if bool(signals.get("undecidable_proved")):
            return Diagnosis(FrontierKind.COMPUTATIONAL, FailureKind.COMPLEXITY_EXCESSIVE, 1.0,
                             ("formal undecidability certificate supplied",))
        if bool(signals.get("missing_data")):
            return Diagnosis(FrontierKind.INFORMATIONAL, FailureKind.INFORMATION_INSUFFICIENT, 0.95,
                             ("required observations/data are absent",))
        if bool(signals.get("objective_underspecified")):
            return Diagnosis(FrontierKind.EPISTEMIC, FailureKind.OBJECTIVE_UNDERSPECIFIED, 0.95,
                             ("optimization or proof target is underspecified",))
        if bool(signals.get("hardware_limit")):
            return Diagnosis(FrontierKind.ARCHITECTURAL, FailureKind.PHYSICAL_RESOURCES_INSUFFICIENT, 0.9,
                             ("resource ceiling reached on the current architecture",))
        if bool(signals.get("representation_sensitive")) or bool(signals.get("poor_conditioning")):
            if bool(signals.get("representation_sensitive")):
                r.append("performance changes materially under representation")
            if bool(signals.get("poor_conditioning")):
                r.append("current coordinates are poorly conditioned")
            return Diagnosis(FrontierKind.REPRESENTATIONAL, FailureKind.REPRESENTATION_INADEQUATE, 0.8,
                             tuple(r))
        if bool(signals.get("complexity_excessive")) or bool(signals.get("termination_unknown")):
            if bool(signals.get("complexity_excessive")):
                r.append("resource growth exceeds configured budget")
            if bool(signals.get("termination_unknown")):
                r.append("termination is operationally unresolved; this is not an undecidability proof")
            return Diagnosis(FrontierKind.COMPUTATIONAL, FailureKind.COMPLEXITY_EXCESSIVE, 0.7,
                             tuple(r))
        if bool(signals.get("proof_absent")):
            return Diagnosis(FrontierKind.LOGICAL, FailureKind.PROOF_ABSENT, 0.55,
                             ("proof is absent; no independence claim is inferred",))
        if bool(signals.get("solver_failure")):
            return Diagnosis(FrontierKind.EPISTEMIC, FailureKind.SOLVER_FAILURE, 0.5,
                             ("solver failed without enough evidence to identify a deeper frontier",))
        return Diagnosis(FrontierKind.UNKNOWN, FailureKind.UNKNOWN_LIMIT, 0.25,
                         ("insufficient evidence to classify the frontier",))

    @classmethod
    def representation_score(cls, candidate: RepresentationCandidate) -> float:
        w = cls.REPRESENTATION_WEIGHTS
        benefit = (
            w["sparsity"] * candidate.sparsity
            + w["verifiability"] * candidate.verifiability
            + w["invariant_retention"] * candidate.invariant_retention
        )
        penalty = (
            w["dimension_cost"] * candidate.dimension_cost
            + w["compute_cost"] * candidate.compute_cost
            + w["reconstruction_error"] * candidate.reconstruction_error
        )
        return benefit - penalty

    @classmethod
    def rank_representations(
        cls, candidates: Iterable[RepresentationCandidate]
    ) -> list[tuple[RepresentationCandidate, float]]:
        ranked = [(candidate, cls.representation_score(candidate)) for candidate in candidates]
        return sorted(ranked, key=lambda item: (-item[1], item[0].name))

    @staticmethod
    def commutator_advantage(cost_ab: float, cost_ba: float) -> float:
        """Operational analogue of Δ_AB = C(B∘A)-C(A∘B).

        Positive means A→B is cheaper than B→A by the returned amount.
        """
        if cost_ab < 0 or cost_ba < 0:
            raise ValueError("costs must be non-negative")
        return cost_ba - cost_ab

    @staticmethod
    def path_score(path: StrategyPath) -> float:
        denominator = path.costs.total
        if denominator == 0:
            return float("inf") if path.verified_gain > 0 else 0.0
        return path.verified_gain / denominator

    def select_path(self, paths: Sequence[StrategyPath]) -> dict[str, object]:
        kept, rejected = self.negative_memory.prune(list(paths))
        if not kept:
            return {"selected": None, "rejected": rejected, "scores": {}}
        scores = {path.signature: self.path_score(path) for path in kept}
        selected = max(kept, key=lambda path: (scores[path.signature], path.signature))
        return {"selected": selected, "rejected": rejected, "scores": scores}

    @staticmethod
    def firewall_check(
        trace: Sequence[str], *, max_depth: int = 8, descent_measure: Sequence[float] | None = None
    ) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if len(trace) > max_depth:
            reasons.append("self_reference_depth_exceeded")
        if len(set(trace)) != len(trace):
            reasons.append("circular_dependency_detected")
        if descent_measure is not None:
            if len(descent_measure) != len(trace):
                reasons.append("descent_measure_length_mismatch")
            elif any(b >= a for a, b in zip(descent_measure, descent_measure[1:])):
                reasons.append("descent_certificate_not_strict")
        return not reasons, tuple(reasons)

    @staticmethod
    def promotion_gate(record: ClaimRecord, target: TruthLevel) -> dict[str, object]:
        allowed, reasons = EpistemicLedger.can_promote(record, target)
        return {
            "allowed": allowed,
            "from_level": int(record.level),
            "target_level": int(target),
            "reasons": list(reasons),
        }

    @classmethod
    def demo_payload(cls) -> dict[str, object]:
        engine = cls()
        reps = [
            RepresentationCandidate("raw", 0.1, 0.8, 0.9, 0.0, 0.5, 1.0),
            RepresentationCandidate("hgfm-cvcd", 0.8, 0.5, 0.35, 0.05, 0.9, 0.95),
            RepresentationCandidate("tensor-lift", 0.65, 0.85, 0.55, 0.02, 0.85, 0.95),
        ]
        ranked = cls.rank_representations(reps)
        diagnosis = cls.diagnose_failure({"representation_sensitive": True, "poor_conditioning": True})
        return {
            "status": "OAK_PROTOTYPE",
            "theory": "Omega-META-GTNT-T-infinity-2",
            "diagnosis": {
                "frontier": diagnosis.frontier.value,
                "failure": diagnosis.failure.value,
                "confidence": diagnosis.confidence,
                "rationale": list(diagnosis.rationale),
            },
            "representations": [
                {"name": rep.name, "score": round(score, 6)} for rep, score in ranked
            ],
            "oak_boundary": [
                "heuristic frontier classification is not an incompleteness proof",
                "termination_unknown is not an undecidability proof",
                "numeric agreement is not a kernel-verified proof",
            ],
        }
