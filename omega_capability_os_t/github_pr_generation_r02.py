from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import CapabilityRequest, _stable_digest
from .github_pr_generation_forest import compile_pr_generation_forest

R02_SCHEMA_VERSION = "0.2.0"

_DECISIONS = {"REUSE", "COMPOSE", "EXTEND", "CREATE_RESIDUAL", "INSPECT"}
_CODE_FAMILIES = {"code", "simplify"}
_SUPPORT_FAMILIES = {
    "reuse",
    "test",
    "benchmark",
    "contract",
    "documentation",
    "provenance",
    "oak",
    "alternative",
}

_FAMILY_OPERATIONS: Mapping[str, str] = {
    "reuse": "INTEGRATE_EXISTING_CAPABILITY",
    "code": "EDIT_OR_ADD_RESIDUAL_IMPLEMENTATION",
    "test": "ADD_OR_STRENGTHEN_TEST",
    "benchmark": "ADD_BOUNDED_BASELINE_BENCHMARK",
    "contract": "EDIT_TYPED_CONTRACT_OR_SCHEMA",
    "documentation": "EDIT_DOCUMENTATION_BOUNDARY",
    "provenance": "ADD_PROVENANCE_OR_EVIDENCE_RECEIPT",
    "oak": "ADD_OAK_OR_M_MINUS_GATE",
    "simplify": "REFACTOR_OR_REMOVE_DUPLICATION",
    "alternative": "ADD_REVIEW_ONLY_ALTERNATIVE_EXPERIMENT",
}

_FAMILY_KIND: Mapping[str, str] = {
    "reuse": "INTEGRATION",
    "code": "SOURCE",
    "test": "TEST",
    "benchmark": "BENCHMARK",
    "contract": "CONTRACT",
    "documentation": "DOCUMENTATION",
    "provenance": "EVIDENCE",
    "oak": "OAK",
    "simplify": "REFACTOR",
    "alternative": "EXPERIMENT",
}

_COMPLEMENT_BONUS: Mapping[frozenset[str], float] = {
    frozenset(("code", "test")): 0.24,
    frozenset(("code", "benchmark")): 0.18,
    frozenset(("reuse", "test")): 0.20,
    frozenset(("reuse", "contract")): 0.16,
    frozenset(("contract", "oak")): 0.18,
    frozenset(("simplify", "test")): 0.22,
    frozenset(("benchmark", "oak")): 0.12,
}

_DECISION_FIT: Mapping[str, Mapping[str, float]] = {
    "REUSE": {
        "reuse": 0.45, "test": 0.16, "benchmark": 0.12, "contract": 0.14,
        "documentation": 0.08, "provenance": 0.12, "oak": 0.14,
        "simplify": 0.12, "alternative": 0.02, "code": -0.80,
    },
    "COMPOSE": {
        "reuse": 0.38, "test": 0.16, "benchmark": 0.12, "contract": 0.24,
        "documentation": 0.08, "provenance": 0.12, "oak": 0.14,
        "simplify": 0.18, "alternative": 0.04, "code": -0.55,
    },
    "EXTEND": {
        "reuse": 0.14, "test": 0.25, "benchmark": 0.20, "contract": 0.18,
        "documentation": 0.08, "provenance": 0.12, "oak": 0.18,
        "simplify": 0.12, "alternative": 0.08, "code": 0.30,
    },
    "CREATE_RESIDUAL": {
        "reuse": -0.04, "test": 0.24, "benchmark": 0.20, "contract": 0.18,
        "documentation": 0.08, "provenance": 0.12, "oak": 0.18,
        "simplify": 0.08, "alternative": 0.12, "code": 0.26,
    },
    "INSPECT": {
        "reuse": 0.12, "test": 0.08, "benchmark": 0.04, "contract": 0.06,
        "documentation": 0.02, "provenance": 0.18, "oak": 0.18,
        "simplify": -0.08, "alternative": 0.02, "code": -1.00,
    },
}


def _dedupe(values: Sequence[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


def _is_path_like(value: str) -> bool:
    value = str(value)
    return "/" in value or value.endswith((".py", ".md", ".json", ".yaml", ".yml", ".toml"))


@dataclass(frozen=True)
class HistoricalGenerationContext:
    request: CapabilityRequest
    pr_genome: Mapping[str, Any]
    decision: str
    decision_basis: str
    selected_capabilities: tuple[str, ...]
    selected_source_refs: tuple[str, ...]
    residual_outputs: tuple[str, ...]
    exact_inspection_refs: tuple[str, ...]
    reuse_coverage_ratio: float
    negative_memory_refs: tuple[str, ...]
    required_tests: tuple[str, ...]
    required_provenance: tuple[str, ...]
    history_enriched: bool
    physical_code_generation_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": {
                "request_id": self.request.request_id,
                "description": self.request.description,
                "domains": list(self.request.domains),
                "consumes": list(self.request.consumes),
                "produces": list(self.request.produces),
            },
            "pr_genome": dict(self.pr_genome),
            "decision": self.decision,
            "decision_basis": self.decision_basis,
            "selected_capabilities": list(self.selected_capabilities),
            "selected_source_refs": list(self.selected_source_refs),
            "residual_outputs": list(self.residual_outputs),
            "exact_inspection_refs": list(self.exact_inspection_refs),
            "reuse_coverage_ratio": self.reuse_coverage_ratio,
            "negative_memory_refs": list(self.negative_memory_refs),
            "required_tests": list(self.required_tests),
            "required_provenance": list(self.required_provenance),
            "history_enriched": self.history_enriched,
            "physical_code_generation_allowed": self.physical_code_generation_allowed,
        }


class HistoricalGenerationContextCompiler:
    """Compile #450 cumulative-intelligence output into generation constraints."""

    @staticmethod
    def _infer_decision(
        selected_capabilities: tuple[str, ...],
        residual_outputs: tuple[str, ...],
        residual_courts: Sequence[Mapping[str, Any]],
    ) -> tuple[str, str]:
        explicit: list[str] = []
        for row in residual_courts:
            residual = row.get("residual", {}) if isinstance(row, Mapping) else {}
            action = str(residual.get("decision") or "")
            if action:
                explicit.append(action)

        if "INSPECT" in explicit:
            return "INSPECT", "fail_closed_due_to_repository_residual_inspection"
        if residual_outputs:
            if selected_capabilities:
                return "EXTEND", "reuse_coalition_covers_part_of_request_residual_remains"
            return "CREATE_RESIDUAL", "no_selected_capability_covers_declared_residual"
        if len(selected_capabilities) > 1:
            return "COMPOSE", "multiple_explicit_capability_contracts_cover_requested_outputs"
        if len(selected_capabilities) == 1:
            return "REUSE", "single_explicit_capability_contract_covers_requested_outputs"
        return "INSPECT", "no_residual_but_no_explicit_reuse_contract_selected"

    def compile(
        self,
        capsule: Mapping[str, Any],
        *,
        target_pr_genome: Mapping[str, Any] | None = None,
    ) -> HistoricalGenerationContext:
        schema = str(capsule.get("schema") or "")
        if not schema.startswith("omega-github-cumulative-intelligence/"):
            raise ValueError("R0.2 requires an omega-github-cumulative-intelligence capsule")

        request = CapabilityRequest.from_dict(capsule.get("request", {}))
        coalition = capsule.get("minimal_reuse_coalition", {})
        if not isinstance(coalition, Mapping):
            raise ValueError("minimal_reuse_coalition must be an object")

        selected = _dedupe(tuple(map(str, coalition.get("selected_capabilities", []))))
        source_refs = _dedupe(tuple(map(str, coalition.get("source_refs", []))))
        residual = _dedupe(tuple(map(str, coalition.get("residual_outputs", []))))
        inspection = _dedupe(tuple(map(str, coalition.get("inspected_pr_candidates", []))))
        coverage = _clamp(float(coalition.get("reuse_coverage_ratio", 0.0)), 0.0, 1.0)

        residual_courts_raw = capsule.get("repository_residual_courts", [])
        residual_courts = tuple(
            row for row in residual_courts_raw if isinstance(row, Mapping)
        )

        tests: list[str] = []
        provenance: list[str] = [*source_refs, *inspection]
        for row in residual_courts:
            residual_row = row.get("residual", {})
            if not isinstance(residual_row, Mapping):
                continue
            tests.extend(map(str, residual_row.get("required_tests", [])))
            provenance.extend(map(str, residual_row.get("required_provenance", [])))

        negative_refs: list[str] = []
        for row in capsule.get("negative_memory_hits", []):
            if isinstance(row, Mapping) and row.get("ref"):
                negative_refs.append(str(row["ref"]))

        decision, basis = self._infer_decision(selected, residual, residual_courts)
        if decision not in _DECISIONS:
            raise AssertionError("internal decision outside R0.2 decision set")

        genome: dict[str, Any]
        if target_pr_genome is not None:
            genome = dict(target_pr_genome)
        else:
            candidates = capsule.get("relevant_pr_genomes", [])
            genome = dict(candidates[0]) if candidates and isinstance(candidates[0], Mapping) else {}
        genome.setdefault("ref", f"pr:context/{request.request_id}#0")
        genome.setdefault("changed_files", [])
        genome.setdefault("named_concepts", [])
        genome.setdefault("intent_tokens", [])

        return HistoricalGenerationContext(
            request=request,
            pr_genome=genome,
            decision=decision,
            decision_basis=basis,
            selected_capabilities=selected,
            selected_source_refs=source_refs,
            residual_outputs=residual,
            exact_inspection_refs=inspection,
            reuse_coverage_ratio=coverage,
            negative_memory_refs=_dedupe(tuple(negative_refs)),
            required_tests=_dedupe(tuple(tests)) or (
                "targeted unit test for each materialized residual",
                "integration test against every reused capability touched by the patch",
                "regression test for the specific historical failure mode when present",
            ),
            required_provenance=_dedupe(tuple(provenance)),
            history_enriched=True,
            physical_code_generation_allowed=decision in {"EXTEND", "CREATE_RESIDUAL"},
        )


@dataclass(frozen=True)
class OutcomeSignal:
    action: str
    sample_count: int
    mean_utility: float
    evidence_refs: tuple[str, ...]
    observational_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _outcome_signal(policy: Mapping[str, Any] | None, decision: str) -> OutcomeSignal:
    action = "CREATE" if decision == "CREATE_RESIDUAL" else decision
    if not policy:
        return OutcomeSignal(action=action, sample_count=0, mean_utility=0.0, evidence_refs=())
    actions = policy.get("actions", {})
    row = actions.get(action, {}) if isinstance(actions, Mapping) else {}
    if not isinstance(row, Mapping):
        row = {}
    refs = _dedupe(tuple(map(str, row.get("evidence_refs", []))))
    n = max(0, int(row.get("n", 0)))
    mean_utility = float(row.get("mean_utility", 0.0)) if n else 0.0
    return OutcomeSignal(
        action=action,
        sample_count=n,
        mean_utility=round(mean_utility, 6),
        evidence_refs=refs,
    )


def _candidate_family(row: Mapping[str, Any]) -> str:
    address = row.get("address", {})
    return str(address.get("family") or "") if isinstance(address, Mapping) else ""


def _eligible_for_contract(
    row: Mapping[str, Any],
    context: HistoricalGenerationContext,
) -> tuple[bool, str]:
    family = _candidate_family(row)
    target = str(row.get("target") or "")
    decision = context.decision

    if decision == "INSPECT":
        return False, "blocked_until_exact_inspection"
    if family == "code":
        if decision not in {"EXTEND", "CREATE_RESIDUAL"}:
            return False, "new_implementation_blocked_by_reuse_first_decision"
        if decision == "EXTEND" and context.residual_outputs:
            changed_files = {str(x) for x in context.pr_genome.get("changed_files", [])}
            if target not in set(context.residual_outputs) and target not in changed_files:
                return False, "extension_code_target_is_not_declared_residual_or_existing_changed_file"
    if family == "simplify" and decision == "CREATE_RESIDUAL":
        return False, "simplification_requires_existing_structure_to_inspect"
    if family not in _CODE_FAMILIES | _SUPPORT_FAMILIES:
        return False, "unsupported_family"
    return True, "eligible_for_review_contract"


def _evaluate_candidates(
    rows: Sequence[Mapping[str, Any]],
    context: HistoricalGenerationContext,
    outcome_signal: OutcomeSignal,
) -> list[dict[str, Any]]:
    evaluated: list[dict[str, Any]] = []
    negative_penalty = min(0.30, 0.03 * len(context.negative_memory_refs))
    empirical_term = (
        0.18 * _clamp(outcome_signal.mean_utility, -2.0, 2.0)
        if outcome_signal.sample_count > 0 and outcome_signal.evidence_refs
        else 0.0
    )

    for row in rows:
        family = _candidate_family(row)
        base = float(row.get("go_gradient_proxy", 0.0))
        fit = float(_DECISION_FIT[context.decision].get(family, -0.50))
        coverage_term = 0.0
        if family == "reuse":
            coverage_term = 0.20 * context.reuse_coverage_ratio
        elif family == "code":
            coverage_term = -0.16 * context.reuse_coverage_ratio

        eligible, gate_reason = _eligible_for_contract(row, context)
        final = base + fit + empirical_term + coverage_term - negative_penalty
        evaluated.append(
            {
                "candidate_id": str(row.get("candidate_id") or ""),
                "family": family,
                "polarity": str((row.get("address") or {}).get("polarity") or ""),
                "target": str(row.get("target") or ""),
                "action": str(row.get("action") or ""),
                "base_go_gradient_proxy": round(base, 6),
                "decision_fit_term": round(fit, 6),
                "empirical_outcome_term": round(empirical_term, 6),
                "reuse_coverage_term": round(coverage_term, 6),
                "negative_memory_penalty": round(negative_penalty, 6),
                "go_gradient_r02_proxy": round(final, 6),
                "eligible_for_review_contract": eligible,
                "gate_reason": gate_reason,
                "pattern_signature": str(row.get("pattern_signature") or ""),
                "materialization_status": "EVALUATED_NOT_CODE",
            }
        )
    evaluated.sort(
        key=lambda item: (
            not item["eligible_for_review_contract"],
            -float(item["go_gradient_r02_proxy"]),
            item["family"],
            item["candidate_id"],
        )
    )
    return evaluated


@dataclass(frozen=True)
class PhysicalPatchContract:
    contract_id: str
    candidate_id: str
    family: str
    kind: str
    operation: str
    target: str
    resolved_target_path: str | None
    decision: str
    source_refs: tuple[str, ...]
    inspection_refs: tuple[str, ...]
    required_tests: tuple[str, ...]
    required_evidence: tuple[str, ...]
    rollback_required: bool
    code_change_generated: bool
    write_authority_granted: bool
    automatic_commit_allowed: bool
    automatic_merge_allowed: bool
    human_review_required: bool
    materialization_status: str
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PhysicalPatchContractCompiler:
    """Compile review contracts only. R0.2 never writes generated source code."""

    def __init__(self, materialization_budget: int = 16) -> None:
        if materialization_budget <= 0:
            raise ValueError("materialization_budget must be positive")
        self.materialization_budget = materialization_budget

    @staticmethod
    def _family_tests(family: str) -> tuple[str, ...]:
        table: Mapping[str, tuple[str, ...]] = {
            "code": ("behavioral regression test for the residual implementation",),
            "test": ("test must fail against a declared negative control or prior defect when applicable",),
            "benchmark": ("same-task baseline and deterministic benchmark metadata",),
            "reuse": ("integration test proving the selected existing capability is compatible",),
            "simplify": ("behavior-preservation regression court",),
            "contract": ("schema/contract validation plus incompatible-input negative control",),
            "oak": ("deterministic falsifier or M-minus regression",),
            "provenance": ("fingerprint/provenance integrity assertion",),
            "documentation": ("documentation claims must not exceed executable/evidence state",),
            "alternative": ("same-task comparison against the incumbent candidate",),
        }
        return table.get(family, ())

    def compile(
        self,
        evaluated: Sequence[Mapping[str, Any]],
        context: HistoricalGenerationContext,
        outcome_signal: OutcomeSignal,
    ) -> tuple[PhysicalPatchContract, ...]:
        if context.decision == "INSPECT":
            return ()

        contracts: list[PhysicalPatchContract] = []
        for row in evaluated:
            if not bool(row.get("eligible_for_review_contract")):
                continue
            family = str(row.get("family") or "")
            target = str(row.get("target") or "")
            refs = _dedupe((*context.selected_source_refs, *context.required_provenance))
            required_tests = _dedupe((*context.required_tests, *self._family_tests(family)))
            required_evidence = _dedupe(
                (
                    *refs,
                    *outcome_signal.evidence_refs,
                    f"candidate:{row.get('candidate_id')}",
                )
            )
            contract_payload = {
                "candidate_id": row.get("candidate_id"),
                "decision": context.decision,
                "family": family,
                "target": target,
                "operation": _FAMILY_OPERATIONS[family],
                "source_refs": refs,
                "inspection_refs": context.exact_inspection_refs,
            }
            contract_id = f"patch-contract:{_stable_digest(contract_payload)[:20]}"
            contracts.append(
                PhysicalPatchContract(
                    contract_id=contract_id,
                    candidate_id=str(row.get("candidate_id") or ""),
                    family=family,
                    kind=_FAMILY_KIND[family],
                    operation=_FAMILY_OPERATIONS[family],
                    target=target,
                    resolved_target_path=target if _is_path_like(target) else None,
                    decision=context.decision,
                    source_refs=refs,
                    inspection_refs=context.exact_inspection_refs,
                    required_tests=required_tests,
                    required_evidence=required_evidence,
                    rollback_required=True,
                    code_change_generated=False,
                    write_authority_granted=False,
                    automatic_commit_allowed=False,
                    automatic_merge_allowed=False,
                    human_review_required=True,
                    materialization_status="REVIEW_CONTRACT_ONLY",
                    boundary=(
                        "A PhysicalPatchContract is a reviewable transformation obligation, not generated code, "
                        "not proof of compatibility, and not authority to write or merge."
                    ),
                )
            )
            if len(contracts) >= self.materialization_budget:
                break
        return tuple(contracts)


def _compile_synergies(
    evaluated: Sequence[Mapping[str, Any]],
    *,
    max_pairs: int = 16,
) -> list[dict[str, Any]]:
    eligible = [row for row in evaluated if row.get("eligible_for_review_contract")][:32]
    pairs: list[dict[str, Any]] = []
    for i, left in enumerate(eligible):
        for right in eligible[i + 1 :]:
            left_family = str(left.get("family") or "")
            right_family = str(right.get("family") or "")
            bonus = _COMPLEMENT_BONUS.get(frozenset((left_family, right_family)), 0.0)
            same_target = str(left.get("target")) == str(right.get("target"))
            if bonus <= 0 and not same_target:
                continue
            base = min(
                float(left.get("go_gradient_r02_proxy", 0.0)),
                float(right.get("go_gradient_r02_proxy", 0.0)),
            )
            synergy = max(0.0, 0.05 * base + bonus + (0.05 if same_target else 0.0))
            pairs.append(
                {
                    "left_candidate_id": left.get("candidate_id"),
                    "right_candidate_id": right.get("candidate_id"),
                    "families": [left_family, right_family],
                    "same_target": same_target,
                    "synergy_proxy": round(synergy, 6),
                    "causal_synergy_proven": False,
                    "boundary": "pair score is a planning proxy, not causal or superadditive proof",
                }
            )
    pairs.sort(
        key=lambda row: (
            -float(row["synergy_proxy"]),
            str(row["left_candidate_id"]),
            str(row["right_candidate_id"]),
        )
    )
    return pairs[:max_pairs]


def compile_pr_generation_r02(
    cumulative_intelligence: Mapping[str, Any],
    *,
    target_pr_genome: Mapping[str, Any] | None = None,
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

    context = HistoricalGenerationContextCompiler().compile(
        cumulative_intelligence,
        target_pr_genome=target_pr_genome,
    )
    signal = _outcome_signal(outcome_policy, context.decision)
    base = compile_pr_generation_forest(
        context.request,
        context.pr_genome,
        generation=generation,
        residual_outputs=context.residual_outputs,
        reuse_coverage_ratio=context.reuse_coverage_ratio,
        materialization_budget=candidate_budget,
        min_go_gradient=min_go_gradient,
    )
    evaluated = _evaluate_candidates(base["compiled_additions"], context, signal)
    contracts = PhysicalPatchContractCompiler(physical_contract_budget).compile(
        evaluated, context, signal
    )
    synergies = _compile_synergies(evaluated)

    empirical_used = signal.sample_count > 0 and bool(signal.evidence_refs)
    code_contract_count = sum(
        row.family in _CODE_FAMILIES for row in contracts
    )
    payload: dict[str, Any] = {
        "schema": f"omega-pr-5k2n-generation-contextual/v{R02_SCHEMA_VERSION}",
        "law": "C_n = 5000 * 2^n",
        "generation": generation,
        "logical_cardinality_decimal": base["logical_cardinality_decimal"],
        "logical_population_materialized": False,
        "historical_context": context.to_dict(),
        "outcome_signal": signal.to_dict(),
        "empirical_outcome_signal_used": empirical_used,
        "base_generation_fingerprint": base["fingerprint"],
        "sampled_candidate_count": base["sampled_candidate_count"],
        "evaluated_candidate_count": len(evaluated),
        "evaluated_candidates": evaluated,
        "synergy_pairs": synergies,
        "physical_patch_contracts": [row.to_dict() for row in contracts],
        "physical_patch_contract_count": len(contracts),
        "code_or_refactor_contract_count": code_contract_count,
        "physical_patch_compiler": {
            "contract_budget": physical_contract_budget,
            "code_change_generated": False,
            "write_authority_granted": False,
            "automatic_commit_allowed": False,
            "automatic_merge_allowed": False,
            "human_review_required": True,
            "history_enriched_required": True,
            "exact_inspection_required": bool(context.exact_inspection_refs),
            "decision_gate": context.decision,
            "code_generation_permitted_by_reuse_gate": context.physical_code_generation_allowed,
        },
        "adaptive_continuation": {
            "architecture_hard_cap": False,
            "current_generation": generation,
            "base_continue_proxy": bool(base["adaptive_continuation"]["continue"]),
            "next_generation_candidate": (
                generation + 1
                if base["adaptive_continuation"]["continue"] and context.decision != "INSPECT"
                else None
            ),
            "rule": (
                "Continue only when bounded candidate value survives reuse-first, OAK and inspection gates. "
                "A runtime generation budget is never a permanent N_max."
            ),
        },
        "oak_boundaries": [
            "cumulative memory != semantic equivalence",
            "reuse outcome history != causal proof",
            "M+ != universal success",
            "M- != universal impossibility",
            "proxy GO gradient != measured engineering value",
            "synergy proxy != causal synergy",
            "PhysicalPatchContract != generated code",
            "contract budget != architectural N_max",
            "5K*2^n logical additions != 5K*2^n physical edits",
            "INSPECT blocks physical contracts even when candidate scores are high",
            "write authority is never inferred from generation scale or CI",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile history-enriched Omega PR 5K2N R0.2 review contracts."
    )
    parser.add_argument("input")
    parser.add_argument("--output", default="-")
    parser.add_argument("--generation", type=int, default=None)
    parser.add_argument("--candidate-budget", type=int, default=None)
    parser.add_argument("--contract-budget", type=int, default=None)
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must be an object")

    generation = args.generation if args.generation is not None else int(payload.get("generation", 0))
    result = compile_pr_generation_r02(
        payload.get("cumulative_intelligence", {}),
        target_pr_genome=payload.get("target_pr_genome"),
        outcome_policy=payload.get("outcome_policy"),
        generation=generation,
        candidate_budget=(
            args.candidate_budget
            if args.candidate_budget is not None
            else int(payload.get("candidate_budget", 64))
        ),
        physical_contract_budget=(
            args.contract_budget
            if args.contract_budget is not None
            else int(payload.get("physical_contract_budget", 16))
        ),
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
