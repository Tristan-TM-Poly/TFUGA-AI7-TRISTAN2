from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .models import ArtifactSpec, RepositorySnapshot, RouteDecision, RouteDecisionRecord


@dataclass(frozen=True, slots=True)
class RepositoryProfile:
    snapshot: RepositorySnapshot
    conceptual_tokens: frozenset[str]
    maturity_score: float

    @classmethod
    def from_snapshot(cls, snapshot: RepositorySnapshot) -> "RepositoryProfile":
        tokens = frozenset(
            token
            for token in re.split(r"[^a-z0-9]+", " ".join((snapshot.name, *snapshot.packages, *snapshot.topics)).lower())
            if len(token) >= 3
        )
        maturity = 0.0
        maturity += min(2.0, len(snapshot.tests) * 0.2)
        maturity += min(2.0, len(snapshot.workflows) * 0.2)
        maturity += min(1.0, len(snapshot.docs) * 0.1)
        maturity += 1.0 if snapshot.writable else 0.0
        maturity -= 3.0 if snapshot.archived else 0.0
        return cls(snapshot=snapshot, conceptual_tokens=tokens, maturity_score=maturity)


class RepoRouter:
    def __init__(self, profiles: Iterable[RepositoryProfile]) -> None:
        self._profiles = tuple(profiles)
        if not self._profiles:
            raise ValueError("at least one repository profile is required")

    @staticmethod
    def _artifact_tokens(artifact: ArtifactSpec) -> set[str]:
        return {
            token
            for token in re.split(
                r"[^a-z0-9]+",
                f"{artifact.creation_id} {artifact.kind} {artifact.suggested_path} {artifact.description}".lower(),
            )
            if len(token) >= 3
        }

    def route(
        self,
        artifact: ArtifactSpec,
        *,
        preferred_repositories: Iterable[str] = (),
    ) -> RouteDecisionRecord:
        preferred = set(preferred_repositories)
        artifact_tokens = self._artifact_tokens(artifact)
        candidates: list[tuple[float, RepositoryProfile, tuple[str, ...]]] = []
        for profile in self._profiles:
            repository = profile.snapshot
            reasons: list[str] = []
            if repository.archived:
                continue
            if artifact.required_visibility == "private_required" and repository.visibility != "private":
                continue
            score = profile.maturity_score
            overlap = len(artifact_tokens.intersection(profile.conceptual_tokens))
            score += overlap * 1.5
            if repository.full_name in preferred:
                score += 6.0
                reasons.append("explicit_candidate_repository")
            if repository.name == "TFUGA-AI7-TRISTAN2":
                score += 2.0
                reasons.append("canonical_integration_repository")
            if artifact.required_visibility == "review_required" and repository.visibility == "private":
                score += 2.0
                reasons.append("private_review_surface")
            if artifact.kind in {"theory", "documentation", "oak_report"} and repository.visibility == "public":
                score += 0.5
                reasons.append("public_documentation_surface")
            if overlap:
                reasons.append(f"conceptual_overlap={overlap}")
            if not repository.writable:
                score -= 10.0
                reasons.append("no_write_permission_observed")
            candidates.append((score, profile, tuple(reasons)))
        if not candidates:
            decision = RouteDecision.KEEP_PRIVATE if artifact.required_visibility == "private_required" else RouteDecision.KEEP_IN_BACKLOG
            return RouteDecisionRecord(
                artifact_id=artifact.artifact_id,
                decision=decision,
                repository=None,
                score=0.0,
                reasons=("no_repository_satisfied_visibility_and_permission_constraints",),
                human_review_required=True,
            )
        candidates.sort(key=lambda item: (-item[0], item[1].snapshot.full_name.lower()))
        best_score, best, reasons = candidates[0]
        alternatives = tuple(item[1].snapshot.full_name for item in candidates[1:4])
        decision = RouteDecision.ADD_TO_EXISTING_REPO
        if best_score < 0:
            decision = RouteDecision.KEEP_IN_BACKLOG
        elif artifact.kind == "code" and best.snapshot.name == "TFUGA-AI7-TRISTAN2":
            decision = RouteDecision.CREATE_SPECIALIZED_PACKAGE
        return RouteDecisionRecord(
            artifact_id=artifact.artifact_id,
            decision=decision,
            repository=best.snapshot.full_name if decision != RouteDecision.KEEP_IN_BACKLOG else None,
            score=round(best_score, 6),
            reasons=reasons or ("deterministic_default_route",),
            alternatives=alternatives,
            human_review_required=True,
        )

    def route_all(
        self,
        artifacts: Iterable[ArtifactSpec],
        *,
        preferred_repositories: Iterable[str] = (),
    ) -> tuple[RouteDecisionRecord, ...]:
        return tuple(
            self.route(artifact, preferred_repositories=preferred_repositories)
            for artifact in artifacts
        )
