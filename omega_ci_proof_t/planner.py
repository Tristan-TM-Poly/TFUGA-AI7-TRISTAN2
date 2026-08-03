from __future__ import annotations

from typing import Any, Mapping, Sequence

from .claims import ClaimRegistry
from .models import ProofPlan, TestSpec, sorted_unique, stable_digest


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "to_dict"):
        result = value.to_dict()
        if isinstance(result, Mapping):
            return result
    raise TypeError("impact plan must be a mapping or expose to_dict()")


class ProofPlanner:
    def __init__(
        self,
        claim_registry: ClaimRegistry,
        test_catalog: Mapping[str, TestSpec],
        *,
        environments: Sequence[str] = ("python-3.10", "python-3.11", "python-3.12", "python-3.13"),
    ) -> None:
        self.claim_registry = claim_registry
        self.test_catalog = dict(test_catalog)
        self.environments = tuple(environments)

    def plan(self, impact_plan: Any) -> ProofPlan:
        impact = _mapping(impact_plan)
        packages = sorted_unique(tuple(str(value) for value in impact.get("affected_packages", ())))
        changed_paths = sorted_unique(tuple(str(value) for value in impact.get("changed_paths", ())))
        claims = self.claim_registry.for_packages(packages)
        claim_ids = tuple(claim.claim_id for claim in claims)
        stale_claim_ids = tuple(claim.claim_id for claim in claims if claim.status in {"PROTOTYPED", "MEASURED"})
        required_ids = self.claim_registry.required_test_ids(claim_ids)
        tests = tuple(self.test_catalog[test_id] for test_id in required_ids if test_id in self.test_catalog)
        missing = tuple(test_id for test_id in required_ids if test_id not in self.test_catalog)
        limitations = [
            "static impact analysis does not exhaustively detect dynamic imports or runtime reflection",
            "software evidence is not a scientific proof",
        ]
        if missing:
            limitations.append("missing tests require generated candidate fixtures before promotion")
        if impact.get("unknown_paths"):
            limitations.append("unknown changed paths require conservative full validation")
        manifest_digest = str(impact.get("manifest_digest") or stable_digest(impact))
        impact_identity = {
            "changed_paths": list(changed_paths),
            "affected_packages": list(packages),
            "unknown_paths": sorted(str(value) for value in impact.get("unknown_paths", ())),
            "manifest_digest": manifest_digest,
        }
        impact_plan_id = str(impact.get("plan_id") or f"IMPACT-{stable_digest(impact_identity)[:20].upper()}")
        completion = (
            "all_required_tests_executed",
            "no_critical_residual",
            "evidence_bundle_integrity_verified",
            "claim_status_not_promoted_beyond_available_evidence",
        )
        return ProofPlan(
            impact_plan_id=impact_plan_id,
            changed_paths=changed_paths,
            affected_packages=packages,
            claim_ids=claim_ids,
            stale_claim_ids=stale_claim_ids,
            tests=tests,
            missing_test_ids=missing,
            environments=self.environments,
            completion_conditions=completion,
            limitations=tuple(limitations),
            manifest_digest=manifest_digest,
        )
