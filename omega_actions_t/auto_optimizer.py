"""Guarded AutoActionOptimizer candidate generation for Ω-ACTIONS-T∞ R0.8."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from .compiler import compile_workflow, validate_ir


def _static_recommendation_ids(evidence: dict[str, Any], workflow_path: str) -> set[str]:
    static = evidence.get("static") or {}
    for workflow in static.get("workflows", []):
        if workflow.get("path") == workflow_path:
            return {str(item.get("id")) for item in workflow.get("recommendations", [])}
    return set()


def _delta_decision(evidence: dict[str, Any], workflow_path: str) -> str | None:
    delta = evidence.get("delta") or {}
    for workflow in delta.get("workflows", []):
        if workflow.get("workflow") == workflow_path:
            return workflow.get("decision")
    return None


def propose_actions(evidence: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
    """Translate evidence into non-destructive candidate actions."""
    proposals: list[dict[str, Any]] = []
    for candidate in (evidence.get("top_candidates") or evidence.get("optimization_candidates") or [])[:limit]:
        path = str(candidate.get("workflow"))
        recs = _static_recommendation_ids(evidence, path)
        delta = _delta_decision(evidence, path)
        actions: list[dict[str, Any]] = []

        if "cancel-obsolete-runs" in recs:
            actions.append({
                "kind": "ADD_CONCURRENCY_CANDIDATE",
                "risk": "medium",
                "automatic_apply": False,
                "reason": "Static evidence indicates a PR/push workflow without concurrency.",
            })
        if "bound-job-runtime" in recs:
            actions.append({
                "kind": "ADD_TIMEOUT_CANDIDATE",
                "risk": "low",
                "automatic_apply": False,
                "reason": "At least one job lacks an explicit runtime bound.",
            })
        if "cache-installation-work" in recs:
            actions.append({
                "kind": "MEASURE_CACHE_VALUE",
                "risk": "low",
                "automatic_apply": False,
                "reason": "Installation work is visible without a cache signal; measure CacheTensor before editing.",
            })
        if delta == "RUN_BROAD_UNROUTED":
            actions.append({
                "kind": "RESEARCH_DELTA_ROUTING",
                "risk": "high",
                "automatic_apply": False,
                "reason": "The workflow is broad/unrouted; explicit dependency/path evidence is required before proposing skips.",
            })
        if actions:
            proposals.append({
                "workflow": path,
                "priority_score": candidate.get("priority_score"),
                "evidence_state": evidence.get("evidence_state"),
                "actions": actions,
            })
    return {
        "schema": "omega-actions-candidates/v0.8",
        "proposal_count": len(proposals),
        "proposals": proposals,
        "automatic_repository_mutation": False,
        "promotion_required": True,
        "oak_limits": [
            "Candidate actions are hypotheses, not authorized repository edits.",
            "Broad trigger routing is research-only until explicit dependency/path evidence exists.",
            "Concurrency cancellation can be unsafe for release, deployment or side-effecting workflows and requires review.",
            "Any compiled candidate must pass the Promotion Gate with comparable before/after evidence.",
        ],
    }


def candidate_ir(
    baseline_ir: dict[str, Any],
    *,
    add_pr_concurrency: bool = False,
) -> dict[str, Any]:
    """Produce a local IR variant without mutating the baseline object."""
    validate_ir(baseline_ir)
    candidate = copy.deepcopy(baseline_ir)
    applied: list[str] = []
    if add_pr_concurrency:
        triggers = candidate.get("on") or {}
        if "pull_request" not in triggers:
            raise ValueError("automatic concurrency candidate is limited to pull_request IR")
        if candidate.get("concurrency"):
            raise ValueError("baseline IR already defines concurrency")
        candidate["concurrency"] = {
            "group": "ci-${{ github.event.pull_request.number || github.ref }}",
            "cancel_in_progress": True,
        }
        applied.append("add_pr_concurrency")
    candidate.setdefault("_omega_candidate", {})
    candidate["_omega_candidate"].update({
        "applied": applied,
        "automatic_apply": False,
        "requires_promotion_gate": True,
    })
    return candidate


def compile_candidate(
    baseline_ir: dict[str, Any],
    *,
    workflow_path: str,
    add_pr_concurrency: bool = False,
) -> dict[str, Any]:
    variant = candidate_ir(baseline_ir, add_pr_concurrency=add_pr_concurrency)
    metadata = variant.pop("_omega_candidate")
    yaml_text = compile_workflow(variant, workflow_path=workflow_path)
    return {
        "schema": "omega-actions-compiled-candidate/v0.8",
        "workflow_path": workflow_path,
        "candidate_ir": variant,
        "candidate_yaml": yaml_text,
        "candidate_metadata": metadata,
        "automatic_repository_mutation": False,
        "promotion_required": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-actions-candidate", description="Generate non-destructive Ω-ACTIONS candidate manifests.")
    parser.add_argument("--evidence", help="Evidence Bundle JSON")
    parser.add_argument("--ir", help="Optional baseline CI IR JSON")
    parser.add_argument("--workflow-path", default=".github/workflows/generated-ci.yml")
    parser.add_argument("--add-pr-concurrency", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if args.ir:
        baseline = json.loads(Path(args.ir).read_text(encoding="utf-8"))
        result = compile_candidate(
            baseline,
            workflow_path=args.workflow_path,
            add_pr_concurrency=args.add_pr_concurrency,
        )
    elif args.evidence:
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        result = propose_actions(evidence)
    else:
        parser.error("one of --evidence or --ir is required")
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
