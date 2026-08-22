"""Omega Tensor Research Compiler R0.6.

R0.6 fuses the GreatSages/DiscoveryPath research compiler with logical
Person-LLMT profiles, ephemeral Shadow projections, sparse tensor coalition
routing, and a typed cognitive instruction set.

A PersonLLMT is a sourced software profile, not a person, consciousness, or
impersonation claim. A Shadow is an ephemeral functional projection. Tensor
routing is sparse and heuristic; no full Cartesian/tensor product is
materialized. Synergy scores are benchmark bookkeeping, not causal proof.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

from sage_tristan.discovery_path_ir import DiscoveryPath, gauss_ceres_reconstruction
from sage_tristan.greatsages import ClaimClass, SageProfile, get_profile
from sage_tristan.greatsages_time_machine import operator_registry
from sage_tristan.representation_noether_compiler import (
    MorphismStatus,
    RepresentationCompiler,
    ceres_representation_compiler,
)


class PermissionScope(str, Enum):
    PUBLIC_ONLY = "public_only"
    CONSENTED_PRIVATE = "consented_private"
    DENY_PRIVATE = "deny_private"


class ShadowRole(str, Enum):
    SOLVER = "solver"
    CRITIC = "critic"
    FORMALIZER = "formalizer"
    COUNTEREXAMPLE = "counterexample"
    REPRESENTATION = "representation"
    EVIDENCE = "evidence"


class ShadowMirror(str, Enum):
    HISTORICAL = "historical"
    MODERN = "modern"
    COMPUTATIONAL = "computational"
    ADVERSARIAL = "adversarial"
    FORMAL = "formal"


class ValueType(str, Enum):
    PROBLEM = "problem"
    REPRESENTATION = "representation"
    CLAIM = "claim"
    OAK_RECEIPT = "oak_receipt"
    ARTIFACT = "artifact"


class Opcode(str, Enum):
    LOAD = "LOAD"
    GATE = "GATE"
    ZOOM = "ZOOM"
    DEZOOM = "DEZOOM"
    REP = "REP"
    CVCD = "CVCD"
    INV = "INV"
    SYM = "SYM"
    APPROX = "APPROX"
    RESIDUAL = "RESIDUAL"
    TRANSFER = "TRANSFER"
    BRANCH = "BRANCH"
    COUNTER = "COUNTER"
    MERGE = "MERGE"
    SIM = "SIM"
    PROVE = "PROVE"
    OAK = "OAK"
    STORE_PLUS = "STORE_PLUS"
    STORE_MINUS = "STORE_MINUS"


class ProgramStatus(str, Enum):
    ADMISSIBLE_SOFTWARE_PROGRAM = "admissible_software_program"
    QUARANTINE = "quarantine"


@dataclass(frozen=True, slots=True)
class PersonLLMT:
    person_id: str
    model_version: str
    corpus_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    operator_ids: tuple[str, ...]
    representation_ids: tuple[str, ...]
    capability_tags: tuple[str, ...]
    temporal_gate_year: int | None = None
    permission_scope: PermissionScope = PermissionScope.PUBLIC_ONLY
    cost: float = 0.2
    risk: float = 0.05
    epistemic_debt: float = 0.0
    model_not_person: bool = True
    historical_mind_certified: bool = False

    def __post_init__(self) -> None:
        if not self.person_id or not self.model_version:
            raise ValueError("person_id and model_version are required")
        if self.cost < 0 or self.risk < 0 or self.epistemic_debt < 0:
            raise ValueError("cost/risk/debt must be non-negative")
        if self.risk > 1:
            raise ValueError("risk must be in [0, 1]")
        if not self.model_not_person:
            raise ValueError("PersonLLMT must preserve model_not_person=True")
        if self.historical_mind_certified:
            raise ValueError("software profile cannot certify a historical mind")
        for values in (
            self.corpus_ids,
            self.source_ids,
            self.operator_ids,
            self.representation_ids,
            self.capability_tags,
        ):
            if len(values) != len(set(values)):
                raise ValueError("PersonLLMT tuple fields must not contain duplicates")


@dataclass(frozen=True, slots=True)
class LLMTRegistry:
    llmts: tuple[PersonLLMT, ...]

    def __post_init__(self) -> None:
        ids = [item.person_id for item in self.llmts]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate PersonLLMT id")

    def get(self, person_id: str) -> PersonLLMT:
        for item in self.llmts:
            if item.person_id == person_id:
                return item
        raise KeyError(person_id)


@dataclass(frozen=True, slots=True)
class ProblemGenome:
    problem_id: str
    capability_tags: tuple[str, ...]
    domain_tags: tuple[str, ...]
    initial_representation_ids: tuple[str, ...]
    target_representation_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    risk_budget: float = 0.5

    def __post_init__(self) -> None:
        if not 0 <= self.risk_budget <= 1:
            raise ValueError("risk_budget must be in [0, 1]")
        if not self.capability_tags:
            raise ValueError("problem requires at least one capability tag")


@dataclass(frozen=True, slots=True)
class ShadowSpec:
    shadow_id: str
    person_id: str
    role: ShadowRole
    domain: str
    temporal_gate_year: int | None
    mirror: ShadowMirror
    operator_ids: tuple[str, ...]
    representation_ids: tuple[str, ...]
    objective: str
    requires_private_data: bool = False
    ephemeral: bool = True
    model_not_person: bool = True

    def __post_init__(self) -> None:
        if not self.ephemeral:
            raise ValueError("R0.6 Shadows are ephemeral by contract")
        if not self.model_not_person:
            raise ValueError("Shadow must preserve model_not_person=True")

    @property
    def coordinate(self) -> tuple[object, ...]:
        return (
            self.person_id,
            self.role.value,
            self.domain,
            self.temporal_gate_year,
            self.mirror.value,
            self.operator_ids,
            self.representation_ids,
            self.objective,
        )


@dataclass(frozen=True, slots=True)
class ShadowFactory:
    registry: LLMTRegistry

    def create(
        self,
        person_id: str,
        *,
        role: ShadowRole,
        domain: str,
        mirror: ShadowMirror,
        operator_ids: Sequence[str],
        representation_ids: Sequence[str],
        objective: str,
        temporal_gate_year: int | None = None,
        requires_private_data: bool = False,
    ) -> ShadowSpec:
        llmt = self.registry.get(person_id)
        requested = set(operator_ids)
        unknown = sorted(requested - set(llmt.operator_ids))
        if unknown:
            raise ValueError(f"shadow requested unsupported operators: {unknown}")
        if requires_private_data and llmt.permission_scope is not PermissionScope.CONSENTED_PRIVATE:
            raise PermissionError("private-data Shadow requires explicit consent scope")
        payload = json.dumps(
            {
                "person": person_id,
                "role": role.value,
                "domain": domain,
                "mirror": mirror.value,
                "operators": tuple(operator_ids),
                "representations": tuple(representation_ids),
                "objective": objective,
                "year": temporal_gate_year,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return ShadowSpec(
            shadow_id="shadow_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
            person_id=person_id,
            role=role,
            domain=domain,
            temporal_gate_year=temporal_gate_year,
            mirror=mirror,
            operator_ids=tuple(operator_ids),
            representation_ids=tuple(representation_ids),
            objective=objective,
            requires_private_data=requires_private_data,
        )


@dataclass(frozen=True, slots=True)
class LLMTMarginal:
    person_id: str
    new_coverage: float
    redundancy: float
    evidence_strength: float
    diversity: float
    cost: float
    risk: float
    marginal_gain: float


@dataclass(frozen=True, slots=True)
class CoalitionReceipt:
    problem_id: str
    selected_person_ids: tuple[str, ...]
    rejected_person_ids: tuple[str, ...]
    covered_capabilities: tuple[str, ...]
    uncovered_capabilities: tuple[str, ...]
    marginals: tuple[LLMTMarginal, ...]
    stop_reason: str
    greedy_heuristic_not_global_optimum: bool = True
    full_tensor_materialized: bool = False


@dataclass(frozen=True, slots=True)
class SparseTensorCoalitionCompiler:
    registry: LLMTRegistry

    @staticmethod
    def _marginal(problem: ProblemGenome, llmt: PersonLLMT, covered: frozenset[str], selected: Sequence[PersonLLMT]) -> LLMTMarginal:
        required = set(problem.capability_tags)
        capabilities = set(llmt.capability_tags)
        newly = (required & capabilities) - set(covered)
        new_coverage = len(newly) / len(required)
        selected_caps = set().union(*(set(item.capability_tags) for item in selected)) if selected else set()
        overlap = len(capabilities & selected_caps)
        redundancy = overlap / max(1, len(capabilities))
        evidence_strength = min(1.0, len(llmt.source_ids) / 3.0)
        diversity = 1.0 - redundancy if selected else 1.0
        marginal = (
            1.70 * new_coverage
            + 0.20 * evidence_strength
            + 0.15 * diversity
            - 0.55 * llmt.cost
            - 0.55 * llmt.risk
            - 0.25 * redundancy
            - 0.10 * min(1.0, llmt.epistemic_debt / 10.0)
        )
        return LLMTMarginal(
            person_id=llmt.person_id,
            new_coverage=round(new_coverage, 6),
            redundancy=round(redundancy, 6),
            evidence_strength=round(evidence_strength, 6),
            diversity=round(diversity, 6),
            cost=llmt.cost,
            risk=llmt.risk,
            marginal_gain=round(marginal, 6),
        )

    def compile(
        self,
        problem: ProblemGenome,
        *,
        max_llmts: int = 4,
        min_marginal_gain: float = 0.05,
    ) -> CoalitionReceipt:
        if max_llmts < 1:
            raise ValueError("max_llmts must be >= 1")
        selected: list[PersonLLMT] = []
        available = list(self.registry.llmts)
        covered: frozenset[str] = frozenset()
        marginals: list[LLMTMarginal] = []
        required = set(problem.capability_tags)
        stop_reason = "no_positive_marginal_gain"

        while available and len(selected) < max_llmts and set(covered) != required:
            scored = [self._marginal(problem, item, covered, selected) for item in available if item.risk <= problem.risk_budget]
            if not scored:
                stop_reason = "risk_budget_or_empty_registry"
                break
            scored.sort(key=lambda item: (-item.marginal_gain, item.person_id))
            best = scored[0]
            if best.marginal_gain < min_marginal_gain:
                stop_reason = "marginal_gain_below_threshold"
                break
            llmt = self.registry.get(best.person_id)
            selected.append(llmt)
            available = [item for item in available if item.person_id != llmt.person_id]
            covered = frozenset(set(covered) | (set(llmt.capability_tags) & required))
            marginals.append(best)
            if set(covered) == required:
                stop_reason = "required_capabilities_covered"
                break
        else:
            if len(selected) >= max_llmts and set(covered) != required:
                stop_reason = "max_llmts_reached"

        selected_ids = tuple(item.person_id for item in selected)
        rejected_ids = tuple(sorted(item.person_id for item in self.registry.llmts if item.person_id not in selected_ids))
        return CoalitionReceipt(
            problem_id=problem.problem_id,
            selected_person_ids=selected_ids,
            rejected_person_ids=rejected_ids,
            covered_capabilities=tuple(sorted(covered)),
            uncovered_capabilities=tuple(sorted(required - set(covered))),
            marginals=tuple(marginals),
            stop_reason=stop_reason,
        )


@dataclass(frozen=True, slots=True)
class Instruction:
    instruction_id: str
    opcode: Opcode
    input_type: ValueType
    output_type: ValueType
    operator_id: str | None = None
    representation_before: tuple[str, ...] = ()
    representation_after: tuple[str, ...] = ()
    cost_budget: float = 0.1
    uncertainty_budget: float = 0.5
    note: str = ""

    def __post_init__(self) -> None:
        if self.cost_budget < 0:
            raise ValueError("instruction cost must be non-negative")
        if not 0 <= self.uncertainty_budget <= 1:
            raise ValueError("instruction uncertainty must be in [0, 1]")


SIGNATURES: Mapping[Opcode, tuple[ValueType, ValueType]] = {
    Opcode.LOAD: (ValueType.PROBLEM, ValueType.PROBLEM),
    Opcode.GATE: (ValueType.PROBLEM, ValueType.PROBLEM),
    Opcode.ZOOM: (ValueType.PROBLEM, ValueType.PROBLEM),
    Opcode.DEZOOM: (ValueType.PROBLEM, ValueType.PROBLEM),
    Opcode.REP: (ValueType.PROBLEM, ValueType.REPRESENTATION),
    Opcode.CVCD: (ValueType.REPRESENTATION, ValueType.REPRESENTATION),
    Opcode.INV: (ValueType.REPRESENTATION, ValueType.CLAIM),
    Opcode.SYM: (ValueType.REPRESENTATION, ValueType.REPRESENTATION),
    Opcode.APPROX: (ValueType.REPRESENTATION, ValueType.REPRESENTATION),
    Opcode.RESIDUAL: (ValueType.REPRESENTATION, ValueType.REPRESENTATION),
    Opcode.TRANSFER: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.BRANCH: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.COUNTER: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.MERGE: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.SIM: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.PROVE: (ValueType.CLAIM, ValueType.CLAIM),
    Opcode.OAK: (ValueType.CLAIM, ValueType.OAK_RECEIPT),
    Opcode.STORE_PLUS: (ValueType.OAK_RECEIPT, ValueType.ARTIFACT),
    Opcode.STORE_MINUS: (ValueType.OAK_RECEIPT, ValueType.ARTIFACT),
}


@dataclass(frozen=True, slots=True)
class CognitiveProgram:
    program_id: str
    problem_id: str
    instructions: tuple[Instruction, ...]
    source_shadow_ids: tuple[str, ...]
    max_cost: float
    max_depth: int
    stop_conditions: tuple[str, ...]

    @property
    def total_declared_cost(self) -> float:
        return round(sum(item.cost_budget for item in self.instructions), 6)


@dataclass(frozen=True, slots=True)
class ProgramAudit:
    program_id: str
    status: ProgramStatus
    type_safe: bool
    budget_safe: bool
    depth_safe: bool
    representation_gate_safe: bool
    unknown_operator_ids: tuple[str, ...]
    quarantined_morphism_ids: tuple[str, ...]
    failures: tuple[str, ...]
    program_is_execution_trace: bool = False


def audit_program(
    program: CognitiveProgram,
    *,
    allowed_operator_ids: Iterable[str],
    representation_compiler: RepresentationCompiler,
) -> ProgramAudit:
    failures: list[str] = []
    current = ValueType.PROBLEM
    type_safe = True
    for instruction in program.instructions:
        expected = SIGNATURES[instruction.opcode]
        if instruction.input_type != expected[0] or instruction.output_type != expected[1] or instruction.input_type != current:
            type_safe = False
            failures.append(f"type mismatch at {instruction.instruction_id}")
        current = instruction.output_type

    budget_safe = program.total_declared_cost <= program.max_cost
    if not budget_safe:
        failures.append("program cost exceeds budget")
    depth_safe = len(program.instructions) <= program.max_depth
    if not depth_safe:
        failures.append("program depth exceeds budget")

    allowed = set(allowed_operator_ids)
    unknown = tuple(sorted({item.operator_id for item in program.instructions if item.operator_id and item.operator_id not in allowed}))
    if unknown:
        failures.append(f"unknown operator ids: {unknown}")

    quarantined: list[str] = []
    representation_gate_safe = True
    for instruction in program.instructions:
        if not instruction.representation_before or not instruction.representation_after:
            continue
        if tuple(sorted(instruction.representation_before)) == tuple(sorted(instruction.representation_after)):
            continue
        matches = representation_compiler.matching(instruction.representation_before, instruction.representation_after)
        if not matches:
            representation_gate_safe = False
            failures.append(f"missing R0.5 morphism for {instruction.instruction_id}")
            continue
        admissible = [item for item in matches if item.status is MorphismStatus.ADMISSIBLE_SOFTWARE_MODEL]
        if not admissible:
            representation_gate_safe = False
            quarantined.extend(item.morphism_id for item in matches)
            failures.append(f"all R0.5 morphisms quarantined for {instruction.instruction_id}")

    return ProgramAudit(
        program_id=program.program_id,
        status=ProgramStatus.ADMISSIBLE_SOFTWARE_PROGRAM if not failures else ProgramStatus.QUARANTINE,
        type_safe=type_safe,
        budget_safe=budget_safe,
        depth_safe=depth_safe,
        representation_gate_safe=representation_gate_safe,
        unknown_operator_ids=unknown,
        quarantined_morphism_ids=tuple(sorted(set(quarantined))),
        failures=tuple(failures),
    )


@dataclass(frozen=True, slots=True)
class ProgramPathReceipt:
    program_id: str
    discovery_path_id: str
    program_operator_ids: tuple[str, ...]
    path_operator_ids: tuple[str, ...]
    exact_operator_trace_match: bool
    program_is_execution_trace: bool = False
    discovery_path_is_runtime_trace: bool = True


def bridge_program_to_ceres_path(program: CognitiveProgram) -> tuple[DiscoveryPath, ProgramPathReceipt]:
    path = gauss_ceres_reconstruction(get_profile("gauss"))
    program_ops = tuple(item.operator_id for item in program.instructions if item.operator_id)
    path_ops = tuple(item.operator_id for item in path.steps)
    receipt = ProgramPathReceipt(
        program_id=program.program_id,
        discovery_path_id=path.path_id,
        program_operator_ids=program_ops,
        path_operator_ids=path_ops,
        exact_operator_trace_match=program_ops == path_ops,
    )
    return path, receipt


@dataclass(frozen=True, slots=True)
class ShadowOutput:
    shadow_id: str
    claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    residual_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TensorMergeReceipt:
    shadow_ids: tuple[str, ...]
    consensus_claim_ids: tuple[str, ...]
    divergent_claim_ids_by_shadow: tuple[tuple[str, tuple[str, ...]], ...]
    unique_evidence_ids: tuple[str, ...]
    evidence_independence_not_inferred: bool = True
    consensus_is_truth: bool = False


def tensor_merge(outputs: Sequence[ShadowOutput]) -> TensorMergeReceipt:
    if not outputs:
        raise ValueError("tensor merge requires at least one output")
    claim_sets = [set(item.claim_ids) for item in outputs]
    consensus = set.intersection(*claim_sets)
    divergent = tuple(
        (item.shadow_id, tuple(sorted(set(item.claim_ids) - consensus)))
        for item in sorted(outputs, key=lambda value: value.shadow_id)
    )
    evidence = tuple(sorted({e for item in outputs for e in item.evidence_ids}))
    return TensorMergeReceipt(
        shadow_ids=tuple(sorted(item.shadow_id for item in outputs)),
        consensus_claim_ids=tuple(sorted(consensus)),
        divergent_claim_ids_by_shadow=divergent,
        unique_evidence_ids=evidence,
    )


@dataclass(frozen=True, slots=True)
class SynergyReceipt:
    left_id: str
    right_id: str
    baseline_quality: float
    left_quality: float
    right_quality: float
    coalition_quality: float
    synergy: float
    causal_synergy_proven: bool = False


def synergy_receipt(left_id: str, right_id: str, *, baseline: float, left: float, right: float, coalition: float) -> SynergyReceipt:
    value = coalition - left - right + baseline
    return SynergyReceipt(left_id, right_id, baseline, left, right, coalition, round(value, 6))


def person_llmt_from_profile(profile: SageProfile) -> PersonLLMT:
    registry = operator_registry(profile)
    representations = tuple(sorted({rep for item in profile.discoveries for rep in item.representations}))
    source_ids = tuple(sorted({source for item in profile.discoveries for source in item.source_ids}))
    capabilities = tuple(sorted(set(profile.cognitive_operators) | set(registry)))
    return PersonLLMT(
        person_id=profile.sage_id,
        model_version="greatsages-r06-logical-profile",
        corpus_ids=tuple(sorted(item.atom_id for item in profile.knowledge)),
        source_ids=source_ids,
        operator_ids=tuple(sorted(registry)),
        representation_ids=representations,
        capability_tags=capabilities,
        temporal_gate_year=profile.death_year,
        permission_scope=PermissionScope.PUBLIC_ONLY,
        cost=0.25,
        risk=0.05,
        epistemic_debt=1.0,
    )


def synthetic_tensor_fixture() -> tuple[LLMTRegistry, ProblemGenome]:
    """Synthetic persons test routing semantics without historical claims."""
    registry = LLMTRegistry(
        (
            PersonLLMT(
                "person_a",
                "synthetic-v1",
                ("corpus_a",),
                ("source_a1", "source_a2"),
                ("representation_switch", "invariant_search"),
                ("native", "latent"),
                ("representation_switch", "invariant_search"),
                cost=0.20,
                risk=0.05,
            ),
            PersonLLMT(
                "person_b",
                "synthetic-v1",
                ("corpus_b",),
                ("source_b1", "source_b2", "source_b3"),
                ("approximation_residual", "anti_invariant_residual"),
                ("latent", "residual"),
                ("residual_control", "counterexample"),
                cost=0.22,
                risk=0.05,
            ),
            PersonLLMT(
                "person_c",
                "synthetic-v1",
                ("corpus_c",),
                ("source_c1",),
                ("representation_switch",),
                ("native",),
                ("representation_switch",),
                cost=0.80,
                risk=0.30,
            ),
        )
    )
    problem = ProblemGenome(
        "synthetic_inverse_problem",
        ("representation_switch", "invariant_search", "residual_control"),
        ("inverse_problem",),
        ("native",),
        ("residual",),
        ("evidence_public",),
        risk_budget=0.5,
    )
    return registry, problem


def ceres_cognitive_program(shadow_ids: Sequence[str] = ()) -> CognitiveProgram:
    instructions = (
        Instruction("r06_load", Opcode.LOAD, ValueType.PROBLEM, ValueType.PROBLEM, cost_budget=0.05),
        Instruction("r06_gate", Opcode.GATE, ValueType.PROBLEM, ValueType.PROBLEM, cost_budget=0.05),
        Instruction(
            "r06_rep",
            Opcode.REP,
            ValueType.PROBLEM,
            ValueType.REPRESENTATION,
            operator_id="representation_switch",
            representation_before=("historical_problem_statement",),
            representation_after=("latent_model", "inverse_problem"),
            cost_budget=0.20,
        ),
        Instruction(
            "r06_approx",
            Opcode.APPROX,
            ValueType.REPRESENTATION,
            ValueType.REPRESENTATION,
            operator_id="approximation_residual",
            representation_before=("latent_model", "inverse_problem"),
            representation_after=("latent_model", "residual_space"),
            cost_budget=0.25,
        ),
        Instruction(
            "r06_inv",
            Opcode.INV,
            ValueType.REPRESENTATION,
            ValueType.CLAIM,
            operator_id="invariant_search",
            representation_before=("latent_model", "residual_space"),
            representation_after=("orbit_reconstruction", "residual_space"),
            cost_budget=0.20,
        ),
        Instruction("r06_oak", Opcode.OAK, ValueType.CLAIM, ValueType.OAK_RECEIPT, cost_budget=0.10),
        Instruction("r06_store", Opcode.STORE_PLUS, ValueType.OAK_RECEIPT, ValueType.ARTIFACT, cost_budget=0.05),
    )
    return CognitiveProgram(
        "ceres_cognitive_program_r06",
        "gauss_1801_ceres",
        instructions,
        tuple(shadow_ids),
        max_cost=1.20,
        max_depth=10,
        stop_conditions=(
            "OAK blocks claim",
            "representation gate fails",
            "marginal verified gain falls below threshold",
            "resource budget exhausted",
        ),
    )


def compile_report() -> dict[str, object]:
    gauss = person_llmt_from_profile(get_profile("gauss"))
    synthetic_registry, problem = synthetic_tensor_fixture()
    coalition = SparseTensorCoalitionCompiler(synthetic_registry).compile(problem, max_llmts=3)
    factory = ShadowFactory(synthetic_registry)
    shadows = tuple(
        factory.create(
            person_id,
            role=ShadowRole.SOLVER if index == 0 else ShadowRole.CRITIC,
            domain="inverse_problem",
            mirror=ShadowMirror.COMPUTATIONAL if index == 0 else ShadowMirror.ADVERSARIAL,
            operator_ids=synthetic_registry.get(person_id).operator_ids,
            representation_ids=synthetic_registry.get(person_id).representation_ids,
            objective="solve_and_falsify_synthetic_problem",
        )
        for index, person_id in enumerate(coalition.selected_person_ids)
    )
    program = ceres_cognitive_program(tuple(item.shadow_id for item in shadows))
    rep_compiler = ceres_representation_compiler()
    gauss_ops = operator_registry(get_profile("gauss"))
    program_audit = audit_program(program, allowed_operator_ids=gauss_ops, representation_compiler=rep_compiler)
    path, path_receipt = bridge_program_to_ceres_path(program)
    outputs = tuple(
        ShadowOutput(
            item.shadow_id,
            ("claim_shared", f"claim_{index}"),
            ("shared_source", f"source_{index}"),
            (f"residual_{index}",),
        )
        for index, item in enumerate(shadows)
    )
    merge = tensor_merge(outputs)
    synergy = synergy_receipt("person_a", "person_b", baseline=0.10, left=0.45, right=0.40, coalition=0.90)
    theoretical_upper_bound = len(synthetic_registry.llmts) * len(ShadowRole) * len(ShadowMirror) * len(Opcode)
    return {
        "engine": "Omega-TENSOR-RESEARCH-COMPILER-T",
        "release": "R0.6",
        "gauss_person_llmt": asdict(gauss),
        "synthetic_coalition": asdict(coalition),
        "shadows": [asdict(item) for item in shadows],
        "sparse_tensor": {
            "materialized_shadow_count": len(shadows),
            "coarse_theoretical_upper_bound": theoretical_upper_bound,
            "full_tensor_materialized": False,
        },
        "cognitive_program": asdict(program),
        "program_audit": asdict(program_audit),
        "program_path_bridge": asdict(path_receipt),
        "discovery_path_id": path.path_id,
        "tensor_merge": asdict(merge),
        "synergy_receipt": asdict(synergy),
        "person_llmt_is_person": False,
        "shadow_is_person": False,
        "shadow_is_ephemeral": True,
        "consensus_is_truth": False,
        "synergy_is_causal_proof": False,
        "full_tensor_expansion_required": False,
        "routing_is_global_optimum_proven": False,
        "r05_representation_backend_required": True,
        "r04_runtime_trace_required": True,
        "oak_note": (
            "R0.6 validates software contracts for logical LLMT profiles, sparse Shadow routing, typed programs, "
            "R0.5 representation gates and an R0.4 trace bridge. It does not certify minds, impersonation fidelity, "
            "causal synergy, scientific truth or global routing optimality."
        ),
    }


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Tensor Research Compiler R0.6")
    parser.add_argument("--report", action="store_true")
    parser.parse_args(argv)
    print(json.dumps(_jsonable(compile_report()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
