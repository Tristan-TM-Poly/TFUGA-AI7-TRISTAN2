from __future__ import annotations

from math import prod
from typing import Any, Mapping, Sequence

from .models import (
    CausalDiagnosis,
    CausalHypothesis,
    CausalObservation,
    HypothesisAssessment,
    shannon_entropy,
)


class CausalDiagnosticEngine:
    """Deterministic heuristic support updater.

    Scores are normalized model-support weights. They are not probabilities of
    real-world causation and never authorize action.
    """

    def __init__(self, hypotheses: Sequence[CausalHypothesis]) -> None:
        if not hypotheses:
            raise ValueError("at least one hypothesis is required")
        ids = [item.hypothesis_id for item in hypotheses]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate hypothesis IDs")
        self.hypotheses = tuple(sorted(hypotheses, key=lambda item: item.hypothesis_id))
        self.by_id = {item.hypothesis_id: item for item in self.hypotheses}

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CausalDiagnosticEngine":
        hypotheses = tuple(
            CausalHypothesis(
                hypothesis_id=str(item["hypothesis_id"]),
                statement=str(item["statement"]),
                cause_node_ids=tuple(str(value) for value in item.get("cause_node_ids", ())),
                prior_weight=float(item.get("prior_weight", 1.0)),
                assumptions=tuple(str(value) for value in item.get("assumptions", ())),
                falsifiers=tuple(str(value) for value in item.get("falsifiers", ())),
                scope=tuple(str(value) for value in item.get("scope", ())),
                severity=str(item.get("severity", "medium")),
            )
            for item in raw.get("hypotheses", ())
        )
        return cls(hypotheses)

    def observations_from_mapping(self, raw: Mapping[str, Any]) -> tuple[CausalObservation, ...]:
        observations = tuple(
            CausalObservation(
                observation_id=str(item["observation_id"]),
                statement=str(item["statement"]),
                likelihood_by_hypothesis={str(key): float(value) for key, value in item["likelihood_by_hypothesis"].items()},
                reliability=float(item.get("reliability", 1.0)),
                source_evidence_ids=tuple(str(value) for value in item.get("source_evidence_ids", ())),
                limitations=tuple(str(value) for value in item.get("limitations", ())),
            )
            for item in raw.get("observations", ())
        )
        for observation in observations:
            unknown = sorted(set(observation.likelihood_by_hypothesis).difference(self.by_id))
            missing = sorted(set(self.by_id).difference(observation.likelihood_by_hypothesis))
            if unknown:
                raise KeyError(f"observation references unknown hypotheses: {', '.join(unknown)}")
            if missing:
                raise KeyError(f"observation omits hypotheses: {', '.join(missing)}")
        return observations

    def diagnose(
        self,
        failure_id: str,
        observations: Sequence[CausalObservation],
        *,
        support_threshold: float = 0.70,
        gap_threshold: float = 0.25,
    ) -> CausalDiagnosis:
        if not failure_id:
            raise ValueError("failure_id is required")
        if not 0.0 <= support_threshold <= 1.0 or not 0.0 <= gap_threshold <= 1.0:
            raise ValueError("thresholds must be in [0, 1]")

        priors = {item.hypothesis_id: item.prior_weight for item in self.hypotheses}
        prior_entropy = shannon_entropy(tuple(priors.values()))
        raw_scores: dict[str, float] = {}
        evidence_for: dict[str, list[str]] = {key: [] for key in priors}
        evidence_against: dict[str, list[str]] = {key: [] for key in priors}

        for hypothesis in self.hypotheses:
            factors = []
            for observation in observations:
                likelihood = observation.likelihood_by_hypothesis[hypothesis.hypothesis_id]
                # Reliability pulls uncertain observations toward a neutral factor.
                adjusted = (likelihood ** observation.reliability) * (0.5 ** (1.0 - observation.reliability))
                factors.append(max(adjusted, 1e-12))
                if likelihood >= 0.67:
                    evidence_for[hypothesis.hypothesis_id].append(observation.observation_id)
                elif likelihood <= 0.33:
                    evidence_against[hypothesis.hypothesis_id].append(observation.observation_id)
            raw_scores[hypothesis.hypothesis_id] = hypothesis.prior_weight * prod(factors or (1.0,))

        total = sum(raw_scores.values())
        if total <= 0:
            normalized = {key: 0.0 for key in raw_scores}
        else:
            normalized = {key: value / total for key, value in raw_scores.items()}
        ordered = sorted(normalized.items(), key=lambda item: (-item[1], item[0]))
        posterior_entropy = shannon_entropy(tuple(normalized.values()))
        top_id = ordered[0][0] if ordered else None
        top_score = ordered[0][1] if ordered else 0.0
        second_score = ordered[1][1] if len(ordered) > 1 else 0.0
        gap = top_score - second_score

        if not observations:
            status = "INSUFFICIENT_EVIDENCE"
        elif all(value <= 1e-10 for value in raw_scores.values()):
            status = "ALL_HYPOTHESES_REFUTED"
        elif top_score >= support_threshold and gap >= gap_threshold:
            status = "HEURISTICALLY_SUPPORTED"
        else:
            status = "AMBIGUOUS"

        assessments = []
        for rank, (hypothesis_id, score) in enumerate(ordered, start=1):
            hypothesis = self.by_id[hypothesis_id]
            assessments.append(HypothesisAssessment(
                hypothesis_id=hypothesis_id,
                support_score=round(score, 12),
                rank=rank,
                evidence_for=tuple(sorted(evidence_for[hypothesis_id])),
                evidence_against=tuple(sorted(evidence_against[hypothesis_id])),
                untested_falsifiers=hypothesis.falsifiers,
                status="leading" if rank == 1 else "alternative",
            ))

        limitations = (
            "normalized support scores are model-relative heuristics, not probabilities of real-world causation",
            "unmodeled causes may exist",
            "observation likelihoods are declared assumptions and require calibration",
            "diagnosis does not authorize code changes or remote actions",
        )
        return CausalDiagnosis(
            failure_id=failure_id,
            assessments=tuple(assessments),
            status=status,
            top_hypothesis_id=top_id,
            support_gap=gap,
            prior_entropy=prior_entropy,
            posterior_entropy=posterior_entropy,
            information_gain=max(0.0, prior_entropy - posterior_entropy),
            limitations=limitations,
        )
