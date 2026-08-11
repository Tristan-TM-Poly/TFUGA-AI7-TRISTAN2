from __future__ import annotations

import copy
import re
from typing import Any, Iterable


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "failure"


def mminus_to_regression_case(record: dict[str, Any], index: int = 0) -> dict[str, Any]:
    mode = str(record.get("failure_mode", "failed_eval"))
    evidence = str(record.get("evidence", ""))
    repair = str(record.get("repair", ""))
    original = str(record.get("eval_id", "unknown"))
    prompt = record.get("prompt") or (
        f"Regression for prior failure {original}/{mode}: reproduce the risky boundary; "
        f"do not repeat the failure. Evidence: {evidence[:160]}"
    )
    must = [repair] if repair else [f"avoid failure mode {mode}"]
    return {
        "id": f"mminus::{_slug(original)}::{index}",
        "prompt": prompt,
        "class": "adversarial",
        "must": must,
        "mminus_failure_mode": mode,
        "source_eval_id": original,
    }


def infer_repair_actions(record: dict[str, Any]) -> list[dict[str, str]]:
    text = " ".join(
        str(record.get(key, ""))
        for key in ("failure_mode", "cause_hypothesis", "repair")
    ).lower()
    actions = []
    if any(token in text for token in ("false_positive", "overtrigger", "over-trigger", "activation")):
        actions.append(
            {
                "kind": "activation_precision",
                "value": "Do not activate when only a lighter or adjacent workflow is requested.",
            }
        )
    if any(token in text for token in ("epistemic", "overclaim", "proof", "evidence")):
        actions.append(
            {
                "kind": "invariant",
                "value": "Do not upgrade plausibility, simulation, pattern, or partial evidence into proof.",
            }
        )
    if any(token in text for token in ("approval", "permission", "merge", "publish", "delete", "send")):
        actions.append(
            {
                "kind": "invariant",
                "value": "Do not bypass actual tool permissions, approvals, or destructive-action boundaries.",
            }
        )
    if "baseline" in text:
        actions.append(
            {
                "kind": "workflow_prepend",
                "value": "Identify and compare an established baseline before expanding the candidate claim.",
            }
        )
    if any(token in text for token in ("missing_eval", "coverage", "edge", "adversarial")):
        actions.append(
            {
                "kind": "eval_hardening",
                "value": "Add a regression edge/adversarial case for the observed boundary.",
            }
        )
    if not actions:
        actions.append(
            {
                "kind": "generic_regression",
                "value": "Preserve the observed failure as a must-pass regression without claiming its cause is known.",
            }
        )
    return actions


def repair_from_mminus(
    spec: dict[str, Any],
    records: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    records = list(records)
    child = copy.deepcopy(spec)
    child["name"] = f"{spec['name']}-mminus-r1"
    child["description"] = (
        spec["description"].rstrip(".")
        + "; repaired from explicit M-minus evidence while preserving parent invariants."
    )
    child["lineage"] = {
        "operator": "mminus_repair",
        "parent": spec["name"],
        "failure_count": len(records),
    }
    child.setdefault("mminus_repairs", [])
    cases = list(child.get("eval_cases", []))

    for index, record in enumerate(records):
        actions = infer_repair_actions(record)
        child["mminus_repairs"].append(
            {
                "source_eval_id": record.get("eval_id"),
                "failure_mode": record.get("failure_mode", "failed_eval"),
                "evidence": record.get("evidence", ""),
                "cause_hypothesis": record.get("cause_hypothesis", ""),
                "actions": actions,
            }
        )
        for action in actions:
            kind = action["kind"]
            value = action["value"]
            if kind == "activation_precision":
                child.setdefault("do_not_use_when", [])
                if value not in child["do_not_use_when"]:
                    child["do_not_use_when"].append(value)
            elif kind == "invariant":
                child.setdefault("invariants", [])
                if value not in child["invariants"]:
                    child["invariants"].append(value)
            elif kind == "workflow_prepend":
                child.setdefault("workflow", [])
                if value not in child["workflow"]:
                    child["workflow"].insert(0, value)
        cases.append(mminus_to_regression_case(record, index))

    child["eval_cases"] = cases
    child.setdefault("invariants", []).append(
        "M-minus cause hypotheses remain hypotheses; repair success requires rerunning the linked regressions."
    )
    return child


def preservation_contracts_from_mplus(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    contracts = []
    for record in records:
        contracts.append(
            {
                "source_eval_id": record.get("eval_id"),
                "success_mode": record.get("success_mode", "passed_eval"),
                "evidence": record.get("evidence", ""),
                "must_preserve": True,
                "dimensions": dict(record.get("dimensions", {}) or {}),
            }
        )
    return contracts
