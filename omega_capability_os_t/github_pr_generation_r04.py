from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import GitHubMemoryIndex, _stable_digest, _tokens

R04_SCHEMA_VERSION = "0.4.0"
_CODE_EXTENSIONS = {".py", ".rs", ".go", ".ts", ".tsx", ".js", ".java", ".cpp", ".c", ".h"}


def _dedupe(values: Sequence[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _is_test_path(path: str) -> bool:
    lower = path.lower()
    name = PurePosixPath(lower).name
    return (
        "/tests/" in f"/{lower}"
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".spec.ts")
        or name.endswith(".test.ts")
        or name.endswith(".test.js")
    )


def _is_workflow_path(path: str) -> bool:
    return path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))


def _is_source_path(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in _CODE_EXTENSIONS and not _is_test_path(path)


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float:
    a, b = set(left), set(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class CompatibilityInspectionReceipt:
    ref: str
    planned_head_sha: str | None
    hydrated_head_sha: str | None
    hydration_status: str
    head_match: bool | None
    changed_files: tuple[str, ...]
    source_files: tuple[str, ...]
    test_files: tuple[str, ...]
    workflow_files: tuple[str, ...]
    python_symbol_assets: tuple[str, ...]
    target_exact_path_overlap: tuple[str, ...]
    intent_overlap_proxy: float
    evidence_class: str
    experiment_eligible: bool
    experiment_block_reason: str
    compatibility_verdict: str
    compatibility_proven: bool
    reuse_authorized: bool
    execution_authorized: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompatibilityExperimentContract:
    experiment_id: str
    candidate_ref: str
    candidate_head_sha: str | None
    target_ref: str
    target_head_sha: str | None
    residual_outputs: tuple[str, ...]
    candidate_source_files: tuple[str, ...]
    candidate_test_files: tuple[str, ...]
    required_checks: tuple[str, ...]
    expected_receipt_fields: tuple[str, ...]
    execution_authorized: bool
    source_mutation_authorized: bool
    reuse_authorized_before_experiment: bool
    human_review_required: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _target_tokens(target_pr_genome: Mapping[str, Any]) -> tuple[str, ...]:
    return _tokens(
        (
            str(target_pr_genome.get("ref") or ""),
            *map(str, target_pr_genome.get("changed_files", [])),
            *map(str, target_pr_genome.get("named_concepts", [])),
            *map(str, target_pr_genome.get("intent_tokens", [])),
        )
    )


def _symbols_for(index: GitHubMemoryIndex, ref: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            asset.asset_id
            for asset in index.assets.values()
            if asset.source_ref == ref and asset.source_kind == "pr_head_python_ast_symbol"
        )
    )


def _head_match(planned: str | None, hydrated: str | None) -> bool | None:
    if not planned or not hydrated:
        return None
    return planned == hydrated


def _hydration_status(
    ref: str,
    hydrated_refs: set[str],
    planned_head: str | None,
    hydrated_head: str | None,
) -> str:
    if ref not in hydrated_refs:
        return "NOT_HYDRATED"
    match = _head_match(planned_head, hydrated_head)
    if match is False:
        return "STALE_HEAD"
    if match is True:
        return "HYDRATED_EXACT_HEAD"
    return "HYDRATED_HEAD_UNVERIFIED"


def _evidence_class(
    status: str,
    source_files: tuple[str, ...],
    test_files: tuple[str, ...],
    workflow_files: tuple[str, ...],
    symbol_assets: tuple[str, ...],
) -> str:
    if status == "STALE_HEAD":
        return "STALE_EVIDENCE"
    if not status.startswith("HYDRATED"):
        return "UNHYDRATED"
    if source_files and test_files and workflow_files and symbol_assets:
        return "STATIC_SOURCE_TEST_CI_SURFACE"
    if source_files and test_files:
        return "STATIC_SOURCE_TEST_SURFACE"
    if source_files or symbol_assets:
        return "STATIC_ONLY"
    return "METADATA_ONLY"


def _experiment_eligibility(
    status: str,
    source_files: tuple[str, ...],
    test_files: tuple[str, ...],
    symbol_assets: tuple[str, ...],
) -> tuple[bool, str]:
    if status != "HYDRATED_EXACT_HEAD":
        return False, "exact_head_hydration_required"
    if not source_files and not symbol_assets:
        return False, "no_technical_source_or_symbol_surface"
    if not test_files:
        return False, "no_candidate_test_surface"
    return True, "exact_head_with_technical_and_test_surface"


def compile_compatibility_inspection_r04(
    r03_report: Mapping[str, Any],
    hydrated_index_payload: Mapping[str, Any],
    hydration_receipt: Mapping[str, Any],
    *,
    target_pr_genome: Mapping[str, Any],
    max_candidates: int = 4,
) -> dict[str, Any]:
    if max_candidates <= 0:
        raise ValueError("max_candidates must be positive")
    if str(r03_report.get("schema") or "") != "omega-pr-5k2n-generation-dual-plane/v0.3.0":
        raise ValueError("R0.4 requires an R0.3 dual-plane report")

    index = GitHubMemoryIndex.from_dict(hydrated_index_payload)
    planned_rows = {
        str(row.get("ref")): row
        for row in r03_report.get("compatibility_inspection_plan", [])
        if isinstance(row, Mapping) and row.get("ref")
    }
    ordered_refs = [
        str(row.get("ref"))
        for row in r03_report.get("compatibility_inspection_plan", [])
        if isinstance(row, Mapping) and row.get("ref")
    ][:max_candidates]
    hydrated_refs = set(map(str, hydration_receipt.get("hydrated_prs", [])))
    target_paths = set(map(str, target_pr_genome.get("changed_files", [])))
    target_tokens = _target_tokens(target_pr_genome)

    receipts: list[CompatibilityInspectionReceipt] = []
    experiments: list[CompatibilityExperimentContract] = []
    for ref in ordered_refs:
        planned = planned_rows.get(ref, {})
        pr = index.prs.get(ref)
        planned_head = str(planned.get("head_sha") or "") or None
        hydrated_head = pr.head_sha if pr else None
        status = _hydration_status(ref, hydrated_refs, planned_head, hydrated_head)
        changed = tuple(pr.files) if pr else ()
        sources = tuple(path for path in changed if _is_source_path(path))
        tests = tuple(path for path in changed if _is_test_path(path))
        workflows = tuple(path for path in changed if _is_workflow_path(path))
        symbols = _symbols_for(index, ref)
        overlap = tuple(sorted(target_paths & set(changed)))
        candidate_tokens = pr.keywords if pr else ()
        intent_overlap = round(_jaccard(target_tokens, candidate_tokens), 6)
        evidence_class = _evidence_class(status, sources, tests, workflows, symbols)
        experiment_eligible, experiment_reason = _experiment_eligibility(status, sources, tests, symbols)
        receipt = CompatibilityInspectionReceipt(
            ref=ref,
            planned_head_sha=planned_head,
            hydrated_head_sha=hydrated_head,
            hydration_status=status,
            head_match=_head_match(planned_head, hydrated_head),
            changed_files=changed,
            source_files=sources,
            test_files=tests,
            workflow_files=workflows,
            python_symbol_assets=symbols,
            target_exact_path_overlap=overlap,
            intent_overlap_proxy=intent_overlap,
            evidence_class=evidence_class,
            experiment_eligible=experiment_eligible,
            experiment_block_reason=experiment_reason,
            compatibility_verdict="UNKNOWN",
            compatibility_proven=False,
            reuse_authorized=False,
            execution_authorized=False,
            boundary=(
                "Exact hydration, source paths, static symbols, test paths and workflow paths improve inspection evidence only. "
                "They do not prove behavioral/interface compatibility or authorize reuse."
            ),
        )
        receipts.append(receipt)

        if experiment_eligible:
            payload = {
                "candidate_ref": ref,
                "candidate_head_sha": hydrated_head,
                "target_ref": target_pr_genome.get("ref"),
                "target_head_sha": target_pr_genome.get("head_sha"),
                "residual_outputs": r03_report.get("artifact_residual_plane", {}).get("residual_outputs", []),
            }
            experiment_id = f"compat-exp:{_stable_digest(payload)[:20]}"
            experiments.append(
                CompatibilityExperimentContract(
                    experiment_id=experiment_id,
                    candidate_ref=ref,
                    candidate_head_sha=hydrated_head,
                    target_ref=str(target_pr_genome.get("ref") or ""),
                    target_head_sha=str(target_pr_genome.get("head_sha") or "") or None,
                    residual_outputs=tuple(
                        map(str, r03_report.get("artifact_residual_plane", {}).get("residual_outputs", []))
                    ),
                    candidate_source_files=sources,
                    candidate_test_files=tests,
                    required_checks=(
                        "inspect candidate source semantics at exact head SHA",
                        "inspect candidate tests and their assumptions at exact head SHA",
                        "compare public interfaces and data contracts against target residual",
                        "run target-specific compatibility tests in a separately authorized isolated court",
                        "record behavior-preserving, incompatible, or unknown outcome with evidence refs",
                        "reject reuse if candidate head changes before experiment completion",
                    ),
                    expected_receipt_fields=(
                        "candidate_ref",
                        "candidate_head_sha",
                        "target_head_sha",
                        "tests_executed",
                        "test_results",
                        "interface_checks",
                        "residual_coverage",
                        "regressions",
                        "evidence_refs",
                        "verdict",
                    ),
                    execution_authorized=False,
                    source_mutation_authorized=False,
                    reuse_authorized_before_experiment=False,
                    human_review_required=True,
                    boundary=(
                        "CompatibilityExperimentContract is a test obligation only. It does not execute candidate code, mutate source, "
                        "or authorize reuse until a fresh evidence-bearing result is reviewed."
                    ),
                )
            )

    errors = [dict(row) for row in hydration_receipt.get("errors", []) if isinstance(row, Mapping)]
    payload: dict[str, Any] = {
        "schema": f"omega-pr-5k2n-compatibility-inspection/v{R04_SCHEMA_VERSION}",
        "target_ref": str(target_pr_genome.get("ref") or ""),
        "target_head_sha": str(target_pr_genome.get("head_sha") or "") or None,
        "artifact_decision_in": r03_report.get("artifact_residual_plane", {}).get("decision"),
        "candidate_budget": max_candidates,
        "planned_candidate_count": len(ordered_refs),
        "hydration_receipt_schema": hydration_receipt.get("schema"),
        "hydrated_candidate_count": len([row for row in receipts if row.hydration_status.startswith("HYDRATED")]),
        "stale_candidate_count": len([row for row in receipts if row.hydration_status == "STALE_HEAD"]),
        "experiment_eligible_candidate_count": len([row for row in receipts if row.experiment_eligible]),
        "hydration_errors": errors,
        "compatibility_receipts": [row.to_dict() for row in receipts],
        "compatibility_experiment_contracts": [row.to_dict() for row in experiments],
        "experiment_contract_count": len(experiments),
        "compatibility_proven_count": 0,
        "reuse_authorized_count": 0,
        "physicalization_gate": "INSPECT",
        "write_authority_granted": False,
        "execution_authorized": False,
        "automatic_commit_allowed": False,
        "automatic_merge_allowed": False,
        "oak_boundaries": [
            "hydrated exact head != compatible behavior",
            "exact head without technical/test surface != experiment-ready",
            "changed-file overlap != semantic equivalence",
            "AST symbol overlap != interface compatibility",
            "test file exists != test passed",
            "workflow file exists != CI passed at candidate head",
            "intent overlap proxy != reuse proof",
            "CompatibilityExperimentContract != experiment execution",
            "no R0.4 static receipt authorizes reuse",
            "candidate head drift invalidates exact-head inspection evidence",
            "CI green for this compiler != compatibility of candidate code",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile exact-hydration compatibility inspection receipts for Omega PR 5K2N R0.4."
    )
    parser.add_argument("r03_report")
    parser.add_argument("hydrated_index")
    parser.add_argument("hydration_receipt")
    parser.add_argument("target_pr_genome")
    parser.add_argument("--max-candidates", type=int, default=4)
    parser.add_argument("--output", default="-")
    args = parser.parse_args(argv)

    def load(path: str) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return value

    report = compile_compatibility_inspection_r04(
        load(args.r03_report),
        load(args.hydrated_index),
        load(args.hydration_receipt),
        target_pr_genome=load(args.target_pr_genome),
        max_candidates=args.max_candidates,
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
