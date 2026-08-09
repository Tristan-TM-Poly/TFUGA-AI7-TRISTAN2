"""R0.4 conservative WorkGraph × ΔCI evidence-subgraph compiler."""
from __future__ import annotations
import hashlib, json
from typing import Any, Iterable

_RUN_DECISIONS = {
    "RUN_EXPLICIT_PATH_MATCH",
    "RUN_PATHS_IGNORE_FALLTHROUGH",
    "RUN_WORKFLOW_SELF_CHANGE",
    "RUN_BROAD_UNROUTED",
}
_EXPLICIT_DECISIONS = {"RUN_EXPLICIT_PATH_MATCH", "RUN_WORKFLOW_SELF_CHANGE"}

def compile_evidence_subgraph(
    delta_report: dict[str, Any],
    *,
    required_workflows: Iterable[str] = (),
) -> dict[str, Any]:
    required = {str(x) for x in required_workflows}
    rows = list(delta_report.get("workflows") or delta_report.get("rows") or [])
    selected: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    safe_skips: list[str] = []

    for row in sorted(rows, key=lambda r: str(r.get("workflow", ""))):
        workflow = str(row.get("workflow") or "")
        decision = str(row.get("decision") or "")
        safe_skip = bool(row.get("safe_skip", False))
        is_required = workflow in required

        if is_required:
            selected.append({
                "workflow": workflow,
                "reason": "REQUIRED_WORKFLOW",
                "decision": decision,
                "matched_files": sorted(row.get("matched_files", [])),
            })
            continue

        if decision in _EXPLICIT_DECISIONS:
            selected.append({
                "workflow": workflow,
                "reason": "EXPLICIT_IMPACT_EVIDENCE",
                "decision": decision,
                "matched_files": sorted(row.get("matched_files", [])),
            })
            continue

        if decision in _RUN_DECISIONS and not safe_skip:
            selected.append({
                "workflow": workflow,
                "reason": "CONSERVATIVE_RUN_UNTIL_DEPENDENCY_PROVEN",
                "decision": decision,
                "matched_files": sorted(row.get("matched_files", [])),
            })
            unresolved.append({
                "workflow": workflow,
                "residue": "RUNNABLE_WITHOUT_EXPLICIT_MINIMALITY_PROOF",
                "decision": decision,
            })
            continue

        if safe_skip:
            safe_skips.append(workflow)

    result = {
        "schema": "omega-workmax-evidence-subgraph/v1",
        "selected_workflows": selected,
        "selected_count": len(selected),
        "safe_skip_workflows": sorted(safe_skips),
        "safe_skip_count": len(safe_skips),
        "unresolved": unresolved,
        "required_workflows": sorted(required),
        "minimality_status": "PROVEN_ONLY_WITHIN_EXPLICIT_ROUTING" if not unresolved else "CONSERVATIVE_NOT_MINIMAL",
        "automatic_skip_authorized": False,
        "automatic_merge_authorized": False,
        "oak_limits": [
            "Broad or negative-filter workflows stay selected until dependency evidence justifies narrowing.",
            "Required checks override compute savings.",
            "Safe path-filter skip is not proof that an omitted workflow is semantically irrelevant outside the declared event.",
            "The result is a proof-preserving candidate subgraph, not a universal minimum.",
        ],
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    result["evidence_subgraph_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result
