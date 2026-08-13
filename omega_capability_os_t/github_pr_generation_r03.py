from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import CapabilityRequest, _stable_digest
from .github_pr_generation_forest import compile_pr_generation_forest
from .github_pr_generation_r02 import (
    HistoricalGenerationContext,
    OutcomeSignal,
    PhysicalPatchContractCompiler,
    _DECISION_FIT,
    _candidate_family,
    _compile_synergies,
    _dedupe,
    _outcome_signal,
)

R03_SCHEMA_VERSION = "0.3.0"

PROCESS_OUTPUTS: tuple[str, ...] = (
    "pr_index",
    "capability_graph",
    "reuse_decision",
    "residual_artifact_spec",
    "llmt_context",
)

ARTIFACT_DECISIONS = {"REUSE", "COMPOSE", "EXTEND", "CREATE_RESIDUAL", "INSPECT"}


def build_process_capability_request(
    target_pr_genome: Mapping[str, Any],
) -> CapabilityRequest:
    ref = str(target_pr_genome.get("ref") or "pr:unknown#0")
    concepts = tuple(map(str, target_pr_genome.get("named_concepts", [])))
    description = "Compile reuse-first prior-PR intelligence and residual contracts for " + ref
    if concepts:
        description += " using " + ", ".join(concepts[:8])
    return CapabilityRequest(
        request_id=f"process-reuse:{ref}",
        description=description,
        domains=("github", "memory", "architecture", "llmt", "software"),
        consumes=("repository", "prior_pr_memory", "capability_registry"),
        produces=PROCESS_OUTPUTS,
    )


def process_request_to_dict(request: CapabilityRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "description": request.description,
        "domains": list(request.domains),
        "consumes": list(request.consumes),
        "produces": list(request.produces),
    }


@dataclass(frozen=True)
class ProcessReusePlane:
    request_outputs: tuple[str, ...]
    selected_capabilities: tuple[str, ...]
    source_refs: tuple[str, ...]
    covered_outputs: tuple[str, ...]
    residual_outputs: tuple[str, ...]
    reuse_coverage_ratio: float
    process_reuse_complete: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactResidualPlane:
    requested_outputs: tuple[str, ...]
    selected_capabilities: tuple[str, ...]
    source_refs: tuple[str, ...]
    contract_covered_outputs: tuple[str, ...]
    residual_outputs: tuple[str, ...]
    historical_candidates: tuple[str, ...]
    heuristic_failure_memory_refs: tuple[str, ...]
    decision: str
    decision_basis: str
    exact_inspection_required: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConfirmedNegativeSignal:
    action: str
    sample_count: int
    failures: int
    evidence_refs: tuple[str, ...]
    penalty: float
    applied: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coalition(capsule: Mapping[str, Any]) -> Mapping[str, Any]:
    row = capsule.get("minimal_reuse_coalition", {})
    if not isinstance(row, Mapping):
        raise ValueError("minimal_reuse_coalition must be an object")
    return row


def _process_plane(process_capsule: Mapping[str, Any]) -> ProcessReusePlane:
    schema = str(process_capsule.get("schema") or "")
    if not schema.startswith("omega-github-cumulative-intelligence/"):
        raise ValueError("process plane requires a cumulative-intelligence capsule")
    coalition = _coalition(process_capsule)
    requested = _dedupe(tuple(map(str, coalition.get("requested_outputs", []))))
    covered = _dedupe(tuple(map(str, coalition.get("contract_covered_outputs", []))))
    residual = _dedupe(tuple(map(str, coalition.get("residual_outputs", []))))
    selected = _dedupe(tuple(map(str, coalition.get("selected_capabilities", []))))
    sources = _dedupe(tuple(map(str, coalition.get("source_refs", []))))
    coverage = max(0.0, min(1.0, float(coalition.get("reuse_coverage_ratio", 0.0))))
    return ProcessReusePlane(
        request_outputs=requested,
        selected_capabilities=selected,
        source_refs=sources,
        covered_outputs=covered,
        residual_outputs=residual,
        reuse_coverage_ratio=round(coverage, 6),
        process_reuse_complete=bool(requested) and not residual and coverage >= 0.999999,
        boundary=(
            "Process-plane reuse means the repository already exposes contracts for the research/generation "
            "workflow. It does not mean the target PR artifact itself is already implemented."
        ),
    )


def _heuristic_failure_refs(artifact_capsule: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for row in artifact_capsule.get("negative_memory_hits", []):
        if isinstance(row, Mapping) and row.get("ref"):
            refs.append(str(row["ref"]))
    return _dedupe(tuple(refs))


def _artifact_plane(artifact_capsule: Mapping[str, Any]) -> ArtifactResidualPlane:
    schema = str(artifact_capsule.get("schema") or "")
    if not schema.startswith("omega-github-cumulative-intelligence/"):
        raise ValueError("artifact plane requires a cumulative-intelligence capsule")
    coalition = _coalition(artifact_capsule)
    requested = _dedupe(tuple(map(str, coalition.get("requested_outputs", []))))
    covered = _dedupe(tuple(map(str, coalition.get("contract_covered_outputs", []))))
    residual = _dedupe(tuple(map(str, coalition.get("residual_outputs", []))))
    selected = _dedupe(tuple(map(str, coalition.get("selected_capabilities", []))))
    sources = _dedupe(tuple(map(str, coalition.get("source_refs", []))))
    candidates = _dedupe(tuple(map(str, coalition.get("inspected_pr_candidates", []))))
    heuristic_refs = _heuristic_failure_refs(artifact_capsule)

    explicit_inspect = False
    for row in artifact_capsule.get("repository_residual_courts", []):
        if not isinstance(row, Mapping):
            continue
        residual_row = row.get("residual", {})
        if isinstance(residual_row, Mapping) and str(residual_row.get("decision") or "") == "INSPECT":
            explicit_inspect = True
            break

    if explicit_inspect:
        decision = "INSPECT"
        basis = "explicit_repository_residual_court_requires_inspection"
    elif residual and selected:
        decision = "EXTEND"
        basis = "explicit_artifact_capability_contracts_cover_part_of_requested_outputs"
    elif not residual and len(selected) > 1:
        decision = "COMPOSE"
        basis = "multiple_explicit_artifact_capability_contracts_cover_requested_outputs"
    elif not residual and len(selected) == 1:
        decision = "REUSE"
        basis = "single_explicit_artifact_capability_contract_covers_requested_outputs"
    elif not selected and candidates:
        decision = "INSPECT"
        basis = "historical_candidates_exist_but_no_artifact_capability_contract_proves_reuse"
    elif residual and not selected and not candidates:
        decision = "CREATE_RESIDUAL"
        basis = "no_explicit_artifact_capability_and_no_prior_candidate_found_in_bounded_history"
    else:
        decision = "INSPECT"
        basis = "ambiguous_artifact_state_fail_closed"

    if decision not in ARTIFACT_DECISIONS:
        raise AssertionError("internal artifact decision outside R0.3 decision set")
    return ArtifactResidualPlane(
        requested_outputs=requested,
        selected_capabilities=selected,
        source_refs=sources,
        contract_covered_outputs=covered,
        residual_outputs=residual,
        historical_candidates=candidates,
        heuristic_failure_memory_refs=heuristic_refs,
        decision=decision,
        decision_basis=basis,
        exact_inspection_required=decision == "INSPECT" or bool(candidates),
        boundary=(
            "Artifact-plane reuse requires explicit artifact Capability contracts or exact compatibility inspection. "
            "Lexical PR candidates and failure-memory regex hits are inspection leads, not proof and not scored M-."
        ),
    )


def _confirmed_negative_signal(
    outcome_policy: Mapping[str, Any] | None,
    decision: str,
) -> ConfirmedNegativeSignal:
    action = "CREATE" if decision == "CREATE_RESIDUAL" else decision
    if not outcome_policy:
        return ConfirmedNegativeSignal(
            action=action,
            sample_count=0,
            failures=0,
            evidence_refs=(),
            penalty=0.0,
            applied=False,
            boundary="No evidence-bearing outcome policy supplied; heuristic failure-memory leads do not alter score.",
        )
    actions = outcome_policy.get("actions", {})
    row = actions.get(action, {}) if isinstance(actions, Mapping) else {}
    if not isinstance(row, Mapping):
        row = {}
    n = max(0, int(row.get("n", 0)))
    failures = max(0, int(row.get("failures", 0)))
    refs = _dedupe(tuple(map(str, row.get("evidence_refs", []))))
    applied = n > 0 and failures > 0 and bool(refs)
    failure_rate = failures / n if n else 0.0
    penalty = min(0.30, 0.24 * failure_rate) if applied else 0.0
    return ConfirmedNegativeSignal(
        action=action,
        sample_count=n,
        failures=failures,
        evidence_refs=refs,
        penalty=round(penalty, 6),
        applied=applied,
        boundary=(
            "Only evidence-bearing observed FAILURE outcomes contribute a numeric negative term. "
            "Regex-derived failure-memory leads remain inspection-only. Outcome association is not causal proof."
        ),
    )


def _required_tests_and_provenance(
    artifact_capsule: Mapping[str, Any],
    artifact: ArtifactResidualPlane,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tests: list[str] = []
    provenance: list[str] = [*artifact.source_refs, *artifact.historical_candidates]
    for row in artifact_capsule.get("repository_residual_courts", []):
        if not isinstance(row, Mapping):
            continue
        residual = row.get("residual", {})
        if not isinstance(residual, Mapping):
            continue
        tests.extend(map(str, residual.get("required_tests", [])))
        provenance.extend(map(str, residual.get("required_provenance", [])))
    if not tests:
        tests.extend(
            (
                "unit test for every residual output",
                "integration test against every reused capability",
                "regression test for each confirmed historical failure reused by the patch",
            )
        )
    return _dedupe(tuple(tests)), _dedupe(tuple(provenance))


def _historical_context(
    artifact_capsule: Mapping[str, Any],
    artifact: ArtifactResidualPlane,
    target_pr_genome: Mapping[str, Any],
) -> HistoricalGenerationContext:
    request = CapabilityRequest.from_dict(artifact_capsule.get("request", {}))
    tests, provenance = _required_tests_and_provenance(artifact_capsule, artifact)
    return HistoricalGenerationContext(
        request=request,
        pr_genome=dict(target_pr_genome),
        decision=artifact.decision,
        decision_basis=artifact.decision_basis,
        selected_capabilities=artifact.selected_capabilities,
        selected_source_refs=artifact.source_refs,
        residual_outputs=artifact.residual_outputs,
        exact_inspection_refs=artifact.historical_candidates,
        reuse_coverage_ratio=(
            len(artifact.contract_covered_outputs) / len(artifact.requested_outputs)
            if artifact.requested_outputs else 0.0
        ),
        negative_memory_refs=(),
        required_tests=tests,
        required_provenance=provenance,
        history_enriched=True,
        physical_code_generation_allowed=artifact.decision in {"EXTEND", "CREATE_RESIDUAL"},
    )


def _evaluate_r03(
    rows: Sequence[Mapping[str, Any]],
    context: HistoricalGenerationContext,
    outcome_signal: OutcomeSignal,
    confirmed_negative: ConfirmedNegativeSignal,
) -> list[dict[str, Any]]:
    empirical_term = (
        0.18 * max(-2.0, min(2.0, outcome_signal.mean_utility))
        if outcome_signal.sample_count > 0 and outcome_signal.evidence_refs
        else 0.0
    )
    evaluated: list[dict[str, Any]] = []
    for row in rows:
        family = _candidate_family(row)
        base = float(row.get("go_gradient_proxy", 0.0))
        fit = float(_DECISION_FIT[context.decision].get(family, -0.50))
        coverage_term = 0.0
        if family == "reuse":
            coverage_term = 0.20 * context.reuse_coverage_ratio
        elif family == "code":
            coverage_term = -0.16 * context.reuse_coverage_ratio

        eligible = True
        reason = "eligible_for_review_contract"
        if context.decision == "INSPECT":
            eligible = False
            reason = "blocked_until_exact_compatibility_inspection"
        elif family == "code" and context.decision not in {"EXTEND", "CREATE_RESIDUAL"}:
            eligible = False
            reason = "new_implementation_blocked_by_artifact_reuse_decision"
        elif family == "code" and context.decision == "EXTEND":
            target = str(row.get("target") or "")
            changed = {str(x) for x in context.pr_genome.get("changed_files", [])}
            if target not in set(context.residual_outputs) and target not in changed:
                eligible = False
                reason = "extension_code_target_is_not_declared_residual_or_changed_file"
        elif family == "simplify" and context.decision == "CREATE_RESIDUAL":
            eligible = False
            reason = "simplification_requires_existing_structure"

        final = base + fit + empirical_term + coverage_term - confirmed_negative.penalty
        evaluated.append(
            {
                "candidate_id": str(row.get("candidate_id") or ""),
                "family": family,
                "polarity": str((row.get("address") or {}).get("polarity") or ""),
                "target": str(row.get("target") or ""),
                "action": str(row.get("action") or ""),
                "base_go_gradient_proxy": round(base, 6),
                "artifact_decision_fit_term": round(fit, 6),
                "empirical_outcome_term": round(empirical_term, 6),
                "artifact_reuse_coverage_term": round(coverage_term, 6),
                "confirmed_m_minus_penalty": confirmed_negative.penalty,
                "heuristic_failure_memory_penalty": 0.0,
                "go_gradient_r03_proxy": round(final, 6),
                "eligible_for_review_contract": eligible,
                "gate_reason": reason,
                "pattern_signature": str(row.get("pattern_signature") or ""),
                "materialization_status": "EVALUATED_NOT_CODE",
            }
        )
    evaluated.sort(
        key=lambda item: (
            not item["eligible_for_review_contract"],
            -float(item["go_gradient_r03_proxy"]),
            item["family"],
            item["candidate_id"],
        )
    )
    return evaluated


def _inspection_plan(
    artifact: ArtifactResidualPlane,
    artifact_capsule: Mapping[str, Any],
    max_items: int = 16,
) -> list[dict[str, Any]]:
    genomes = {
        str(row.get("ref")): row
        for row in artifact_capsule.get("relevant_pr_genomes", [])
        if isinstance(row, Mapping) and row.get("ref")
    }
    rows: list[dict[str, Any]] = []
    for rank, ref in enumerate(artifact.historical_candidates[:max_items], start=1):
        genome = genomes.get(ref, {})
        rows.append(
            {
                "rank": rank,
                "ref": ref,
                "head_sha": genome.get("head_sha"),
                "changed_files": list(genome.get("changed_files", [])),
                "symbol_assets": list(genome.get("symbol_assets", [])),
                "inspection_status": "NOT_EXECUTED",
                "required_checks": [
                    "fetch exact source at recorded head SHA",
                    "inspect changed files and public symbols",
                    "inspect tests and CI evidence at that head",
                    "compare interface/behavior contract against target residual",
                    "record compatibility, incompatibility, or unknown with evidence refs",
                ],
                "compatibility_proven": False,
                "reuse_authorized": False,
                "boundary": "retrieval rank is an inspection priority, not compatibility or reuse proof",
            }
        )
    return rows


def compile_pr_generation_r03(
    artifact_cumulative_intelligence: Mapping[str, Any],
    process_cumulative_intelligence: Mapping[str, Any],
    *,
    target_pr_genome: Mapping[str, Any],
    outcome_policy: Mapping[str, Any] | None = None,
    generation: int = 0,
    candidate_budget: int = 64,
    physical_contract_budget: int = 16,
    min_go_gradient: float = 1.0,
) -> dict[str, Any]:
    if generation < 0:
        raise ValueError("generation must be >= 0")
    if candidate_budget <= 0 or physical_contract_budget <= 0:
        raise ValueError("budgets must be positive")

    process = _process_plane(process_cumulative_intelligence)
    artifact = _artifact_plane(artifact_cumulative_intelligence)
    context = _historical_context(artifact_cumulative_intelligence, artifact, target_pr_genome)
    outcome_signal = _outcome_signal(outcome_policy, artifact.decision)
    confirmed_negative = _confirmed_negative_signal(outcome_policy, artifact.decision)

    base = compile_pr_generation_forest(
        context.request,
        target_pr_genome,
        generation=generation,
        residual_outputs=artifact.residual_outputs,
        reuse_coverage_ratio=context.reuse_coverage_ratio,
        materialization_budget=candidate_budget,
        min_go_gradient=min_go_gradient,
    )
    evaluated = _evaluate_r03(
        base["compiled_additions"], context, outcome_signal, confirmed_negative
    )
    contracts = PhysicalPatchContractCompiler(physical_contract_budget).compile(
        evaluated, context, outcome_signal
    )
    synergies = _compile_synergies(evaluated)
    inspections = _inspection_plan(artifact, artifact_cumulative_intelligence)

    payload: dict[str, Any] = {
        "schema": f"omega-pr-5k2n-generation-dual-plane/v{R03_SCHEMA_VERSION}",
        "law": "C_n = 5000 * 2^n",
        "generation": generation,
        "logical_cardinality_decimal": base["logical_cardinality_decimal"],
        "logical_population_materialized": False,
        "process_reuse_plane": process.to_dict(),
        "artifact_residual_plane": artifact.to_dict(),
        "outcome_signal": outcome_signal.to_dict(),
        "confirmed_negative_signal": confirmed_negative.to_dict(),
        "heuristic_failure_memory_numeric_penalty": 0.0,
        "compatibility_inspection_plan": inspections,
        "base_generation_fingerprint": base["fingerprint"],
        "sampled_candidate_count": base["sampled_candidate_count"],
        "evaluated_candidate_count": len(evaluated),
        "evaluated_candidates": evaluated,
        "synergy_pairs": synergies,
        "physical_patch_contracts": [row.to_dict() for row in contracts],
        "physical_patch_contract_count": len(contracts),
        "physical_patch_compiler": {
            "contract_budget": physical_contract_budget,
            "code_change_generated": False,
            "write_authority_granted": False,
            "automatic_commit_allowed": False,
            "automatic_merge_allowed": False,
            "human_review_required": True,
            "artifact_decision_gate": artifact.decision,
            "process_reuse_complete": process.process_reuse_complete,
            "exact_compatibility_inspection_required": artifact.exact_inspection_required,
        },
        "adaptive_continuation": {
            "architecture_hard_cap": False,
            "current_generation": generation,
            "next_generation_candidate": (
                generation + 1
                if bool(base["adaptive_continuation"]["continue"])
                and artifact.decision != "INSPECT"
                else None
            ),
            "rule": (
                "Process-plane reuse can be complete while artifact-plane reuse remains unresolved. "
                "Do not continue physicalization through an INSPECT gate."
            ),
        },
        "oak_boundaries": [
            "process capability reuse != artifact implementation reuse",
            "generic deliverable token != capability contract output",
            "historical candidate != compatible implementation",
            "regex failure-memory lead != confirmed M-",
            "only evidence-bearing observed failures may alter the numeric negative term",
            "M+ or M- outcome association != causal proof",
            "INSPECT blocks PhysicalPatchContracts regardless of generation score",
            "PhysicalPatchContract != source patch",
            "5K*2^n logical candidates != 5K*2^n physical edits",
            "process reuse coverage 1.0 != target artifact completeness",
            "CI green != external truth",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile dual-plane Omega PR 5K2N R0.3 review contracts."
    )
    parser.add_argument("input")
    parser.add_argument("--output", default="-")
    parser.add_argument("--generation", type=int, default=None)
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must be an object")
    generation = args.generation if args.generation is not None else int(payload.get("generation", 0))
    result = compile_pr_generation_r03(
        payload.get("artifact_cumulative_intelligence", {}),
        payload.get("process_cumulative_intelligence", {}),
        target_pr_genome=payload.get("target_pr_genome", {}),
        outcome_policy=payload.get("outcome_policy"),
        generation=generation,
        candidate_budget=int(payload.get("candidate_budget", 64)),
        physical_contract_budget=int(payload.get("physical_contract_budget", 16)),
        min_go_gradient=float(payload.get("min_go_gradient", 1.0)),
    )
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(encoded, end="")
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
