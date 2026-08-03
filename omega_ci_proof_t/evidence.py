from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    ArtifactEvidence,
    EvidenceBundle,
    EvidenceDecision,
    ProofPlan,
    TestResult,
)


def hash_file(path: str | Path) -> ArtifactEvidence:
    file_path = Path(path)
    payload = file_path.read_bytes()
    return ArtifactEvidence(
        path=file_path.as_posix(),
        sha256=sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )


class EvidenceBundleBuilder:
    def build(
        self,
        plan: ProofPlan,
        *,
        run_id: str,
        commit_sha: str,
        environment: Mapping[str, Any],
        test_results: Sequence[TestResult],
        properties: Mapping[str, bool],
        artifacts: Iterable[ArtifactEvidence] = (),
        parent_bundle_ids: Sequence[str] = (),
    ) -> EvidenceBundle:
        required_ids = {test.test_id for test in plan.tests}
        observed = {result.test_id: result for result in test_results}
        missing_results = sorted(required_ids.difference(observed))
        failed = sorted(test_id for test_id, result in observed.items() if result.status != "PASSED")
        property_failures = sorted(key for key, value in properties.items() if not value)
        reasons: list[str] = []
        if missing_results:
            reasons.append(f"missing test results: {', '.join(missing_results)}")
        if plan.missing_test_ids:
            reasons.append(f"missing test specifications: {', '.join(plan.missing_test_ids)}")
        if failed:
            reasons.append(f"failed tests: {', '.join(failed)}")
        if property_failures:
            reasons.append(f"failed properties: {', '.join(property_failures)}")
        promotion_allowed = not reasons and bool(plan.claim_ids)
        decision = EvidenceDecision(
            status="MEASURED_SOFTWARE_FIXTURE" if promotion_allowed else "BLOCKED",
            promotion_allowed=promotion_allowed,
            automatic_merge_allowed=False,
            human_review_required=True,
            reasons=tuple(reasons or ["human review remains required in autonomy levels A1-A3"]),
        )
        return EvidenceBundle(
            run_id=run_id,
            commit_sha=commit_sha,
            proof_plan_id=plan.plan_id,
            proof_plan_digest=plan.digest,
            environment=dict(environment),
            subject={
                "affected_packages": list(plan.affected_packages),
                "changed_paths": list(plan.changed_paths),
            },
            claims_tested=plan.claim_ids,
            test_results=tuple(test_results),
            properties=dict(properties),
            artifacts=tuple(artifacts),
            limitations=plan.limitations,
            decision=decision,
            parent_bundle_ids=tuple(parent_bundle_ids),
        )


class EvidenceVerifier:
    def verify_serialized(self, raw: Mapping[str, Any], *, required_test_ids: Sequence[str] = ()) -> tuple[bool, tuple[str, ...]]:
        from .io import evidence_bundle_from_mapping

        bundle = evidence_bundle_from_mapping(raw)
        ok, errors = self.verify(bundle, required_test_ids=required_test_ids)
        extra = list(errors)
        if raw.get("merkle_root") != bundle.merkle_root:
            extra.append("declared Merkle root does not match recalculated root")
        if raw.get("bundle_id") != bundle.bundle_id:
            extra.append("declared bundle ID does not match recalculated identity")
        return (ok and not extra, tuple(extra))

    def verify(self, bundle: EvidenceBundle, *, required_test_ids: Sequence[str] = ()) -> tuple[bool, tuple[str, ...]]:
        errors: list[str] = []
        if bundle.decision.automatic_merge_allowed:
            errors.append("automatic merge must remain disabled for A1-A3")
        if not bundle.proof_plan_digest:
            errors.append("proof plan digest is required")
        ids = [result.test_id for result in bundle.test_results]
        if len(ids) != len(set(ids)):
            errors.append("duplicate test result IDs")
        missing = sorted(set(required_test_ids).difference(ids))
        if missing:
            errors.append(f"required tests absent: {', '.join(missing)}")
        for artifact in bundle.artifacts:
            path = Path(artifact.path)
            if path.exists():
                payload = path.read_bytes()
                if sha256(payload).hexdigest() != artifact.sha256 or len(payload) != artifact.size_bytes:
                    errors.append(f"artifact integrity mismatch: {artifact.path}")
        if not bundle.merkle_root:
            errors.append("Merkle root missing")
        return (not errors, tuple(errors))
