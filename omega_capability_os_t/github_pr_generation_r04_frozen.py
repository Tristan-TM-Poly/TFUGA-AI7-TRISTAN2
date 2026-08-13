from __future__ import annotations

from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import _stable_digest

FROZEN_SCHEMA_VERSION = "0.1.0"
FROZEN_SEED_SCHEMA = f"omega-pr-5k2n-r04-frozen-static-seed/v{FROZEN_SCHEMA_VERSION}"
R04_SCHEMA = "omega-pr-5k2n-compatibility-inspection/v0.4.0"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    raise ValueError("expected list-like frozen seed field")


def compile_frozen_r04_hold(
    frozen_seed: Mapping[str, Any],
    *,
    target_pr_genome: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebind frozen static R0.4 evidence to the current target in HOLD mode.

    Frozen static evidence is useful for inspection continuity under API outage,
    but it is never allowed to emit a compatibility experiment. If the target
    head changed since the source run, the stale context is explicit.
    """

    schema = str(frozen_seed.get("schema") or "")
    if schema != FROZEN_SEED_SCHEMA:
        raise ValueError(f"unsupported frozen R0.4 seed schema: {schema}")

    target_ref = str(target_pr_genome.get("ref") or "")
    target_head_sha = str(target_pr_genome.get("head_sha") or "") or None
    source_target_head_sha = str(frozen_seed.get("source_target_head_sha") or "") or None
    context_fresh = bool(
        target_head_sha
        and source_target_head_sha
        and target_head_sha == source_target_head_sha
    )

    receipts: list[dict[str, Any]] = []
    for raw in _as_list(frozen_seed.get("receipts")):
        if not isinstance(raw, Mapping):
            raise ValueError("frozen receipt must be an object")
        reason = (
            "frozen_static_seed_requires_live_revalidation"
            if context_fresh
            else "stale_target_inspection_context"
        )
        receipt = {
            "ref": str(raw.get("ref") or ""),
            "planned_head_sha": str(raw.get("planned_head_sha") or "") or None,
            "hydrated_head_sha": str(raw.get("hydrated_head_sha") or "") or None,
            "hydration_status": str(raw.get("hydration_status") or "NOT_HYDRATED"),
            "head_match": raw.get("head_match"),
            "changed_files": list(map(str, _as_list(raw.get("changed_files")))),
            "source_files": list(map(str, _as_list(raw.get("source_files")))),
            "test_files": list(map(str, _as_list(raw.get("test_files")))),
            "workflow_files": list(map(str, _as_list(raw.get("workflow_files")))),
            "python_symbol_assets": list(map(str, _as_list(raw.get("python_symbol_assets")))),
            "target_exact_path_overlap": [],
            "intent_overlap_proxy": float(raw.get("intent_overlap_proxy", 0.0)),
            "evidence_class": str(raw.get("evidence_class") or "METADATA_ONLY"),
            "experiment_eligible": False,
            "experiment_block_reason": reason,
            "compatibility_verdict": "UNKNOWN",
            "compatibility_proven": False,
            "reuse_authorized": False,
            "execution_authorized": False,
            "boundary": (
                "Frozen exact-head candidate evidence is historical inspection continuity only. "
                "It cannot authorize an experiment or reuse without current live target-context revalidation."
            ),
        }
        receipts.append(receipt)

    payload: dict[str, Any] = {
        "schema": R04_SCHEMA,
        "target_ref": target_ref,
        "target_head_sha": target_head_sha,
        "artifact_decision_in": str(frozen_seed.get("artifact_decision") or "INSPECT"),
        "candidate_budget": len(receipts),
        "planned_candidate_count": len(receipts),
        "hydration_receipt_schema": "frozen-static-fallback",
        "hydrated_candidate_count": sum(
            str(row["hydration_status"]).startswith("HYDRATED") for row in receipts
        ),
        "stale_candidate_count": sum(
            row["hydration_status"] == "STALE_HEAD" for row in receipts
        ),
        "experiment_eligible_candidate_count": 0,
        "hydration_errors": [],
        "compatibility_receipts": receipts,
        "compatibility_experiment_contracts": [],
        "experiment_contract_count": 0,
        "compatibility_proven_count": 0,
        "reuse_authorized_count": 0,
        "physicalization_gate": "INSPECT",
        "write_authority_granted": False,
        "execution_authorized": False,
        "automatic_commit_allowed": False,
        "automatic_merge_allowed": False,
        "frozen_fallback": True,
        "current_live_history_complete": False,
        "inspection_context_source_head_sha": source_target_head_sha,
        "inspection_context_fresh": context_fresh,
        "source_r04_fingerprint": str(frozen_seed.get("source_r04_fingerprint") or ""),
        "source_workflow_run_id": int(frozen_seed.get("source_workflow_run_id", 0)),
        "source_artifact_id": int(frozen_seed.get("source_artifact_id", 0)),
        "source_artifact_sha256": str(frozen_seed.get("source_artifact_sha256") or ""),
        "residual_outputs": list(map(str, _as_list(frozen_seed.get("residual_outputs")))),
        "oak_boundaries": [
            "frozen static seed != current live GitHub history",
            "historical candidate hydration != current target compatibility",
            "stale target inspection context blocks experiment eligibility",
            "fresh target equality alone would still require live revalidation",
            "hydrated exact candidate head != compatible behavior",
            "changed-file overlap != semantic equivalence",
            "AST symbol overlap != interface compatibility",
            "test file exists != test passed",
            "workflow file exists != CI passed at candidate head",
            "no frozen fallback receipt authorizes reuse or execution",
            "API outage must degrade to INSPECT/HOLD, not CREATE or REUSE",
            "CI green for fallback compiler != compatibility of candidate code",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile stale-safe frozen Omega PR 5K2N R0.4 HOLD evidence."
    )
    parser.add_argument("seed")
    parser.add_argument("target_pr_genome")
    parser.add_argument("--output", default="-")
    args = parser.parse_args(argv)

    def load(path: str) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return value

    report = compile_frozen_r04_hold(
        load(args.seed),
        target_pr_genome=load(args.target_pr_genome),
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(encoded, end="")
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
