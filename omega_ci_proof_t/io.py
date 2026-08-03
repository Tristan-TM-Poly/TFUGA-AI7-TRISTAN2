from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import (
    ArtifactEvidence,
    EvidenceBundle,
    EvidenceDecision,
    ProofPlan,
    TestResult,
    TestSpec,
)


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_catalog_from_mapping(raw: Mapping[str, Any]) -> dict[str, TestSpec]:
    tests = raw.get("tests", [])
    return {
        str(item["test_id"]): TestSpec(
            test_id=str(item["test_id"]),
            kind=str(item["kind"]),
            target=str(item["target"]),
            command=str(item["command"]),
            description=str(item["description"]),
            source_claim_ids=tuple(str(value) for value in item.get("source_claim_ids", [])),
            generated=bool(item.get("generated", False)),
            source_rule_id=str(item.get("source_rule_id", "")),
        )
        for item in tests
    }


def proof_plan_from_mapping(raw: Mapping[str, Any]) -> ProofPlan:
    return ProofPlan(
        impact_plan_id=str(raw["impact_plan_id"]),
        changed_paths=tuple(raw.get("changed_paths", [])),
        affected_packages=tuple(raw.get("affected_packages", [])),
        claim_ids=tuple(raw.get("claim_ids", [])),
        stale_claim_ids=tuple(raw.get("stale_claim_ids", [])),
        tests=tuple(TestSpec(
            test_id=str(item["test_id"]), kind=str(item["kind"]), target=str(item["target"]),
            command=str(item["command"]), description=str(item["description"]),
            source_claim_ids=tuple(item.get("source_claim_ids", [])), generated=bool(item.get("generated", False)),
            source_rule_id=str(item.get("source_rule_id", "")),
        ) for item in raw.get("tests", [])),
        missing_test_ids=tuple(raw.get("missing_test_ids", [])),
        environments=tuple(raw.get("environments", [])),
        completion_conditions=tuple(raw.get("completion_conditions", [])),
        limitations=tuple(raw.get("limitations", [])),
        manifest_digest=str(raw["manifest_digest"]),
    )


def evidence_bundle_from_mapping(raw: Mapping[str, Any]) -> EvidenceBundle:
    return EvidenceBundle(
        run_id=str(raw["run_id"]), commit_sha=str(raw["commit_sha"]),
        proof_plan_id=str(raw["proof_plan_id"]), proof_plan_digest=str(raw["proof_plan_digest"]),
        environment=dict(raw.get("environment", {})), subject=dict(raw.get("subject", {})),
        claims_tested=tuple(raw.get("claims_tested", [])),
        test_results=tuple(TestResult(**item) for item in raw.get("test_results", [])),
        properties=dict(raw.get("properties", {})),
        artifacts=tuple(ArtifactEvidence(**item) for item in raw.get("artifacts", [])),
        limitations=tuple(raw.get("limitations", [])),
        decision=EvidenceDecision(
            status=str(raw["decision"]["status"]), promotion_allowed=bool(raw["decision"]["promotion_allowed"]),
            automatic_merge_allowed=bool(raw["decision"].get("automatic_merge_allowed", False)),
            human_review_required=bool(raw["decision"].get("human_review_required", True)),
            reasons=tuple(raw["decision"].get("reasons", [])),
        ),
        parent_bundle_ids=tuple(raw.get("parent_bundle_ids", [])),
    )
