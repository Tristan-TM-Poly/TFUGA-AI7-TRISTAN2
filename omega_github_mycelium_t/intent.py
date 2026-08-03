from __future__ import annotations

import re
from typing import Iterable

from .models import IntentContract, sha256_digest


_DEFAULT_OUTPUTS = (
    "theory",
    "system_graph",
    "documentation",
    "code",
    "tests",
    "benchmark",
    "evidence",
    "oak_report",
    "product_hypothesis",
    "ip_report",
)

_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("documentation", "document", "claim"), "omega-doc-t"),
    (("space", "spatial", "satellite", "cubesat"), "omega-space-systems-t"),
    (("energy", "énergie", "microgrid"), "omega-energy-t"),
    (("transform", "ffwt", "wavelet", "ondelette"), "omega-transform-t"),
    (("web", "crawler", "site"), "omega-web-hg-t"),
    (("protein", "protéine", "fold"), "omega-protein-fold-t"),
    (("organic", "molécule", "molecule"), "omega-org-fam-t"),
    (("github", "pull request", "pr", "repository", "dépôt"), "oakgate-github-factory"),
    (("uncertainty", "incertitude"), "omega-unc2-t"),
    (("revenue", "revenu", "company", "entreprise"), "omega-rev-t"),
)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "intent"


class IntentCompiler:
    """Compile a human objective into a deterministic dry-run campaign contract."""

    def infer_root_creation(self, objective: str) -> str:
        lowered = objective.lower()
        best: tuple[int, str] | None = None
        for keywords, creation in _KEYWORDS:
            score = sum(1 for keyword in keywords if keyword in lowered)
            if score and (best is None or score > best[0]):
                best = (score, creation)
        return best[1] if best else "hgfm"

    def compile(
        self,
        objective: str,
        *,
        root_creation: str | None = None,
        expected_outputs: Iterable[str] = _DEFAULT_OUTPUTS,
        candidate_repositories: Iterable[str] = (),
        constraints: Iterable[str] = (),
        success_conditions: Iterable[str] = (),
        requested_depth_mode: str = "adaptive",
        observed_depth_target: int | None = None,
        author: str = "Tristan",
    ) -> IntentContract:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective cannot be empty")
        creation = root_creation or self.infer_root_creation(objective)
        material = {
            "objective": objective,
            "root_creation": creation,
            "outputs": tuple(expected_outputs),
            "repositories": tuple(candidate_repositories),
            "constraints": tuple(constraints),
            "success": tuple(success_conditions),
            "depth_mode": requested_depth_mode,
            "depth_target": observed_depth_target,
        }
        intent_id = f"intent.{_slug(creation)}.{sha256_digest(material)[:16]}"
        default_constraints = (
            "dry_run_remote_mutations",
            "provenance_required",
            "human_gate_for_irreversible_actions",
            "ip_and_visibility_review",
            "no_automatic_merge",
        )
        default_success = (
            "campaign_graph_is_acyclic",
            "every_artifact_has_a_route_or_explicit_backlog_reason",
            "oak_report_emitted",
            "rollback_plan_present",
        )
        return IntentContract(
            intent_id=intent_id,
            objective=objective,
            root_creation=creation,
            expected_outputs=tuple(expected_outputs),
            candidate_repositories=tuple(candidate_repositories),
            constraints=tuple(default_constraints) + tuple(constraints),
            success_conditions=tuple(default_success) + tuple(success_conditions),
            requested_depth_mode=requested_depth_mode,
            observed_depth_target=observed_depth_target,
            author=author,
            remote_mutations_authorized=False,
            metadata={"compiler": "omega-github-mycelium-r0.1"},
        )
