"""OAK promotion gates and evidence-graph validation for R∞ candidates."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

from .models import AntiPatternSpec, EvidenceArtifact, EvidenceLevel, FormCandidateRInf


@dataclass(frozen=True)
class PromotionRequirement:
    level: EvidenceLevel
    required_checks: tuple[str, ...]
    forbidden_unresolved_risks: tuple[str, ...]
    minimum_independent_artifacts: int = 0


PROMOTION_REQUIREMENTS: dict[EvidenceLevel, PromotionRequirement] = {
    EvidenceLevel.VISUAL_PATTERN: PromotionRequirement(EvidenceLevel.VISUAL_PATTERN, (), ()),
    EvidenceLevel.OBSERVED_FIT: PromotionRequirement(
        EvidenceLevel.OBSERVED_FIT,
        ("observed_exact_or_tolerance_fit", "domain_declared"),
        ("domain_error",),
    ),
    EvidenceLevel.HELD_OUT_PREDICTION: PromotionRequirement(
        EvidenceLevel.HELD_OUT_PREDICTION,
        ("observed_fit", "heldout_all_match", "training_holdout_separated"),
        ("vacuous_interpolation", "high_order_memorization"),
    ),
    EvidenceLevel.ADVERSARIAL_VALIDATION: PromotionRequirement(
        EvidenceLevel.ADVERSARIAL_VALIDATION,
        ("heldout_prediction", "remote_indices", "mutation_suite", "competing_models"),
        ("finite_search_as_proof", "precision_hallucination"),
        minimum_independent_artifacts=1,
    ),
    EvidenceLevel.SYMBOLIC_IDENTITY: PromotionRequirement(
        EvidenceLevel.SYMBOLIC_IDENTITY,
        ("symbolic_substitution", "domain_and_singularities", "initial_conditions"),
        ("numerical_to_exact", "illegal_exchange", "branch_cut"),
        minimum_independent_artifacts=1,
    ),
    EvidenceLevel.MATHEMATICAL_PROOF: PromotionRequirement(
        EvidenceLevel.MATHEMATICAL_PROOF,
        ("complete_argument", "all_quantifiers_scoped", "assumptions_explicit"),
        ("finite_search_as_proof", "formal_placeholder"),
        minimum_independent_artifacts=1,
    ),
    EvidenceLevel.FORMAL_PROOF: PromotionRequirement(
        EvidenceLevel.FORMAL_PROOF,
        ("proof_assistant_accepts", "no_placeholders", "statement_matches_claim"),
        ("formal_placeholder",),
        minimum_independent_artifacts=1,
    ),
}


@dataclass(frozen=True)
class PromotionDecision:
    candidate_id: str
    requested_level: EvidenceLevel
    granted_level: EvidenceLevel
    accepted: bool
    missing_checks: tuple[str, ...]
    blocking_risks: tuple[str, ...]
    blocking_antipatterns: tuple[str, ...]
    evidence_artifacts: int
    independent_artifacts: int
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "requested_level": int(self.requested_level),
            "requested_label": self.requested_level.name,
            "granted_level": int(self.granted_level),
            "granted_label": self.granted_level.name,
            "accepted": self.accepted,
            "missing_checks": list(self.missing_checks),
            "blocking_risks": list(self.blocking_risks),
            "blocking_antipatterns": list(self.blocking_antipatterns),
            "evidence_artifacts": self.evidence_artifacts,
            "independent_artifacts": self.independent_artifacts,
            "reasons": list(self.reasons),
        }


@dataclass
class EvidenceGraph:
    artifacts: dict[str, EvidenceArtifact] = field(default_factory=dict)
    dependencies: dict[str, set[str]] = field(default_factory=dict)

    def add(self, artifact: EvidenceArtifact, depends_on: Sequence[str] = ()) -> None:
        if artifact.artifact_id in self.artifacts and self.artifacts[artifact.artifact_id] != artifact:
            raise ValueError(f"artifact ID collision: {artifact.artifact_id}")
        unknown = [item for item in depends_on if item not in self.artifacts]
        if unknown:
            raise KeyError(f"unknown dependency artifacts: {unknown}")
        self.artifacts[artifact.artifact_id] = artifact
        self.dependencies.setdefault(artifact.artifact_id, set()).update(depends_on)
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(node: str) -> None:
            if node in permanent:
                return
            if node in temporary:
                raise ValueError("evidence graph contains a cycle")
            temporary.add(node)
            for dependency in self.dependencies.get(node, ()):
                visit(dependency)
            temporary.remove(node)
            permanent.add(node)

        for node in self.artifacts:
            visit(node)

    def closure(self, artifact_ids: Iterable[str]) -> set[str]:
        result: set[str] = set()

        def visit(node: str) -> None:
            if node in result:
                return
            if node not in self.artifacts:
                raise KeyError(node)
            result.add(node)
            for dependency in self.dependencies.get(node, ()):
                visit(dependency)

        for artifact_id in artifact_ids:
            visit(artifact_id)
        return result

    def digest(self) -> str:
        payload = {
            "artifacts": {key: self.artifacts[key].digest for key in sorted(self.artifacts)},
            "dependencies": {key: sorted(self.dependencies.get(key, ())) for key in sorted(self.artifacts)},
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


def _automatic_checks(candidate: FormCandidateRInf) -> set[str]:
    checks = {"domain_declared"} if candidate.assumptions else set()
    if candidate.observed_fit:
        checks.update({"observed_exact_or_tolerance_fit", "observed_fit"})
    if candidate.held_out_prediction:
        checks.update({"heldout_all_match", "heldout_prediction", "training_holdout_separated"})
    if candidate.adversarial_validation:
        checks.update({"remote_indices", "mutation_suite", "competing_models"})
    if candidate.global_identity_proved:
        checks.update({"complete_argument", "all_quantifiers_scoped", "assumptions_explicit"})
    if candidate.formal_proof_completed:
        checks.update({"proof_assistant_accepts", "no_placeholders", "statement_matches_claim"})
    return checks


def evaluate_promotion(
    candidate: FormCandidateRInf,
    requested_level: EvidenceLevel,
    *,
    completed_checks: Iterable[str] = (),
    unresolved_risks: Iterable[str] = (),
    antipattern_hits: Iterable[AntiPatternSpec] = (),
    independent_provenance: Iterable[str] = (),
) -> PromotionDecision:
    if requested_level < EvidenceLevel.VISUAL_PATTERN or requested_level > EvidenceLevel.FORMAL_PROOF:
        raise ValueError("requested evidence level outside OAK ladder")

    checks = _automatic_checks(candidate) | set(completed_checks)
    risks = set(candidate.risk_tags) | set(unresolved_risks)
    hits = tuple(antipattern_hits)
    independent = {item for item in independent_provenance if item}

    granted = EvidenceLevel.VISUAL_PATTERN
    missing_for_requested: tuple[str, ...] = ()
    blocking_risks: tuple[str, ...] = ()
    blocking_hits: tuple[str, ...] = ()
    reasons: list[str] = []

    for level in EvidenceLevel:
        if level > requested_level:
            break
        requirement = PROMOTION_REQUIREMENTS[level]
        missing = tuple(item for item in requirement.required_checks if item not in checks)
        blocked_risks = tuple(item for item in requirement.forbidden_unresolved_risks if item in risks)
        blocked_hits = tuple(
            item.antipattern_id
            for item in hits
            if item.blocks_promotion_above < level
        )
        insufficient_independent = len(independent) < requirement.minimum_independent_artifacts
        if missing or blocked_risks or blocked_hits or insufficient_independent:
            missing_for_requested = missing
            blocking_risks = blocked_risks
            blocking_hits = blocked_hits
            if insufficient_independent:
                reasons.append(
                    f"level {level.name} requires {requirement.minimum_independent_artifacts} independent artifact(s)"
                )
            break
        granted = level

    if requested_level >= EvidenceLevel.MATHEMATICAL_PROOF and not candidate.global_identity_proved:
        granted = min(granted, EvidenceLevel.SYMBOLIC_IDENTITY)
        reasons.append("candidate does not carry a global proof artifact")
    if requested_level >= EvidenceLevel.FORMAL_PROOF and not candidate.formal_proof_completed:
        granted = min(granted, EvidenceLevel.MATHEMATICAL_PROOF)
        reasons.append("candidate does not carry a completed formal proof")

    accepted = granted >= requested_level
    if missing_for_requested:
        reasons.append("required checks are missing")
    if blocking_risks:
        reasons.append("unresolved risks block promotion")
    if blocking_hits:
        reasons.append("negative-memory anti-patterns block promotion")
    if accepted:
        reasons.append("all requirements for requested level are satisfied")

    return PromotionDecision(
        candidate_id=candidate.candidate_id,
        requested_level=requested_level,
        granted_level=granted,
        accepted=accepted,
        missing_checks=missing_for_requested,
        blocking_risks=blocking_risks,
        blocking_antipatterns=blocking_hits,
        evidence_artifacts=len(candidate.evidence),
        independent_artifacts=len(independent),
        reasons=tuple(reasons),
    )


def validate_candidate_consistency(candidate: FormCandidateRInf) -> list[str]:
    errors: list[str] = []
    if candidate.evidence_level >= EvidenceLevel.OBSERVED_FIT and not candidate.observed_fit:
        errors.append("OAK-1 requires complete observed fit")
    if candidate.evidence_level >= EvidenceLevel.HELD_OUT_PREDICTION and not candidate.held_out_prediction:
        errors.append("OAK-2 requires complete held-out prediction")
    if candidate.evidence_level >= EvidenceLevel.ADVERSARIAL_VALIDATION and not candidate.adversarial_validation:
        errors.append("OAK-3 requires complete declared adversarial checks")
    if candidate.evidence_level >= EvidenceLevel.MATHEMATICAL_PROOF and not candidate.global_identity_proved:
        errors.append("OAK-5 requires global_identity_proved")
    if candidate.evidence_level >= EvidenceLevel.FORMAL_PROOF and not candidate.formal_proof_completed:
        errors.append("OAK-6 requires formal_proof_completed")
    return errors
