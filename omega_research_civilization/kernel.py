from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Mapping, Sequence

from omega_morphogenesis import EpistemicStatus, MorphogenesisKernel, Residual


class ResearchUnitKind(str, Enum):
    UNIVERSITY = "university"
    RESEARCH_GROUP = "research_group"
    VIRTUAL_TRISTAN = "virtual_tristan"
    AIT = "ait"
    LLMT = "llmt"
    ALLT = "allt"
    SIMULATION_LAB = "simulation_lab"
    SCIENTIFIC_COURT = "scientific_court"
    VERIFIER = "verifier"


@dataclass(frozen=True)
class CompilationPolicy:
    """Finite policy for JIT research-civilization generation."""

    max_depth: int = 3
    max_materialized_units: int = 12
    minimum_spawn_margin: float = 0.15
    minimum_unit_utility: float = 0.10
    high_complexity_threshold: float = 0.70

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_materialized_units < 3:
            raise ValueError("max_materialized_units must be >= 3")


@dataclass(frozen=True)
class ResearchUnit:
    unit_id: str
    kind: ResearchUnitKind
    role: str
    depth: int
    capabilities: tuple[str, ...]
    parent_id: str | None = None
    materialized: bool = True
    expected_verified_gain: float = 0.0
    complexity_rent: float = 0.0
    compute_cost: float = 0.0

    def utility_margin(self) -> float:
        return self.expected_verified_gain - self.complexity_rent - self.compute_cost


@dataclass(frozen=True)
class CivilizationPlan:
    question: str
    residual_ids: tuple[str, ...]
    units: tuple[ResearchUnit, ...]
    policy: CompilationPolicy
    version: str = "0.1.0"

    def materialized_units(self) -> tuple[ResearchUnit, ...]:
        return tuple(unit for unit in self.units if unit.materialized)

    def potential_units(self) -> tuple[ResearchUnit, ...]:
        return tuple(unit for unit in self.units if not unit.materialized)

    def digest(self) -> str:
        payload = {
            "question": self.question,
            "residual_ids": self.residual_ids,
            "units": [
                {**asdict(unit), "kind": unit.kind.value}
                for unit in self.units
            ],
            "policy": asdict(self.policy),
            "version": self.version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    statement: str
    producer_id: str
    falsifier_id: str
    verifier_id: str
    output_status: EpistemicStatus
    evidence_status: EpistemicStatus
    provenance: tuple[str, ...]
    tests: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimDecision:
    accepted: bool
    verified: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ResearchSeed:
    """BOOK0-like minimum seed for deterministic reconstruction."""

    question: str
    residual_ids: tuple[str, ...]
    unit_blueprints: tuple[tuple[str, str, str, int, tuple[str, ...], str | None], ...]
    verified_claims: tuple[
        tuple[str, str, int, int, str, str, str, tuple[str, ...], tuple[str, ...]], ...
    ]
    policy: CompilationPolicy
    source_plan_hash: str
    version: str = "0.1.0"

    def digest(self) -> str:
        payload = {
            "question": self.question,
            "residual_ids": self.residual_ids,
            "unit_blueprints": self.unit_blueprints,
            "verified_claims": self.verified_claims,
            "policy": asdict(self.policy),
            "source_plan_hash": self.source_plan_hash,
            "version": self.version,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


class ResearchCivilizationKernel:
    """Question -> minimum finite research civilization -> evidence -> BOOK0 seed.

    The kernel plans and verifies. It intentionally performs no external actions.
    """

    _CONTROL_ROLES = frozenset({"generator", "falsifier", "verifier"})

    def __init__(self, morphogenesis: MorphogenesisKernel | None = None) -> None:
        self.morphogenesis = morphogenesis or MorphogenesisKernel()

    @staticmethod
    def should_spawn_subcivilization(
        *,
        expected_verified_gain: float,
        complexity_rent: float,
        compute_cost: float,
        depth: int,
        policy: CompilationPolicy,
    ) -> bool:
        if depth >= policy.max_depth:
            return False
        margin = expected_verified_gain - complexity_rent - compute_cost
        return margin > policy.minimum_spawn_margin

    def compile(
        self,
        question: str,
        residuals: Iterable[Residual] = (),
        *,
        policy: CompilationPolicy | None = None,
        complexity_signal: float = 0.0,
    ) -> CivilizationPlan:
        question = question.strip()
        if not question:
            raise ValueError("question is required")
        policy = policy or CompilationPolicy()
        ranked = self.morphogenesis.rank_residuals(residuals)
        residual_ids = tuple(r.residual_id for r in ranked)

        units: list[ResearchUnit] = [
            ResearchUnit(
                "vt-generator",
                ResearchUnitKind.VIRTUAL_TRISTAN,
                "generator",
                0,
                ("hypothesis_generation", "representation_search"),
                expected_verified_gain=1.0,
            ),
            ResearchUnit(
                "vt-falsifier",
                ResearchUnitKind.VIRTUAL_TRISTAN,
                "falsifier",
                0,
                ("counterexample_search", "assumption_attack"),
                expected_verified_gain=0.9,
            ),
            ResearchUnit(
                "independent-verifier",
                ResearchUnitKind.VERIFIER,
                "verifier",
                0,
                ("evidence_audit", "replay", "claim_scope_check"),
                expected_verified_gain=1.0,
            ),
        ]

        if ranked:
            top = ranked[0]
            gain = min(1.5, max(top.priority(), 0.0))
            materialized = self.should_spawn_subcivilization(
                expected_verified_gain=gain,
                complexity_rent=0.10,
                compute_cost=0.05,
                depth=0,
                policy=policy,
            )
            units.append(
                ResearchUnit(
                    "ait-solver",
                    ResearchUnitKind.AIT,
                    "solver",
                    1,
                    ("task_decomposition", "tool_routing"),
                    expected_verified_gain=gain,
                    complexity_rent=0.10,
                    compute_cost=0.05,
                    materialized=materialized,
                )
            )

        if complexity_signal >= policy.high_complexity_threshold:
            candidate_gain = min(1.5, 0.6 + complexity_signal)
            can_spawn = self.should_spawn_subcivilization(
                expected_verified_gain=candidate_gain,
                complexity_rent=0.45,
                compute_cost=0.20,
                depth=0,
                policy=policy,
            )
            units.extend(
                [
                    ResearchUnit(
                        "research-group-1",
                        ResearchUnitKind.RESEARCH_GROUP,
                        "coordination",
                        1,
                        ("parallel_research", "synthesis"),
                        expected_verified_gain=candidate_gain,
                        complexity_rent=0.45,
                        compute_cost=0.20,
                        materialized=can_spawn,
                    ),
                    ResearchUnit(
                        "virtual-university-1",
                        ResearchUnitKind.UNIVERSITY,
                        "institutional_shell",
                        2,
                        ("multi_group_coordination", "curriculum_generation"),
                        parent_id="research-group-1",
                        expected_verified_gain=max(0.0, complexity_signal),
                        complexity_rent=0.75,
                        compute_cost=0.30,
                        materialized=False,
                    ),
                    ResearchUnit(
                        "simulation-lab-1",
                        ResearchUnitKind.SIMULATION_LAB,
                        "simulation",
                        1,
                        ("counterfactual_simulation",),
                        expected_verified_gain=0.55 + 0.5 * complexity_signal,
                        complexity_rent=0.25,
                        compute_cost=0.20,
                        materialized=False,
                    ),
                ]
            )

        if len([u for u in units if u.materialized]) > policy.max_materialized_units:
            raise ValueError("compiled plan exceeds materialization budget")
        return CivilizationPlan(question, residual_ids, tuple(units), policy)

    def materialize(self, plan: CivilizationPlan, unit_id: str) -> CivilizationPlan:
        current = list(plan.units)
        by_id = {u.unit_id: u for u in current}
        if unit_id not in by_id:
            raise KeyError(unit_id)
        target = by_id[unit_id]
        if target.materialized:
            return plan
        if len(plan.materialized_units()) >= plan.policy.max_materialized_units:
            return plan
        if not self.should_spawn_subcivilization(
            expected_verified_gain=target.expected_verified_gain,
            complexity_rent=target.complexity_rent,
            compute_cost=target.compute_cost,
            depth=max(0, target.depth - 1),
            policy=plan.policy,
        ):
            return plan
        if target.parent_id and not by_id[target.parent_id].materialized:
            return plan

        replacement = ResearchUnit(**{**asdict(target), "materialized": True})
        updated = tuple(replacement if u.unit_id == unit_id else u for u in current)
        return CivilizationPlan(plan.question, plan.residual_ids, updated, plan.policy, plan.version)

    @staticmethod
    def judge_claim(claim: ClaimRecord) -> ClaimDecision:
        reasons: list[str] = []
        ids = {claim.producer_id, claim.falsifier_id, claim.verifier_id}
        if len(ids) != 3:
            reasons.append("Generator, falsifier, and verifier must be independent identities")
        if not claim.provenance:
            reasons.append("provenance is required")
        if not claim.tests:
            reasons.append("at least one discriminating test is required")
        if claim.output_status == EpistemicStatus.FALSIFIED:
            return ClaimDecision(True, False, tuple(reasons))
        if claim.evidence_status == EpistemicStatus.FALSIFIED:
            reasons.append("falsified evidence cannot support promotion")
        if claim.output_status > claim.evidence_status:
            reasons.append("epistemic inflation: claim exceeds supporting evidence")

        accepted = not reasons
        verified = accepted and claim.evidence_status >= EpistemicStatus.OBSERVED
        return ClaimDecision(accepted, verified, tuple(reasons))

    def prune(
        self,
        plan: CivilizationPlan,
        unit_utilities: Mapping[str, float],
    ) -> CivilizationPlan:
        kept: list[ResearchUnit] = []
        for unit in plan.units:
            if unit.role in self._CONTROL_ROLES:
                kept.append(unit)
                continue
            utility = unit_utilities.get(unit.unit_id, unit.utility_margin())
            if utility >= plan.policy.minimum_unit_utility:
                kept.append(unit)
        kept_ids = {u.unit_id for u in kept}
        kept = [u for u in kept if u.parent_id is None or u.parent_id in kept_ids]
        return CivilizationPlan(plan.question, plan.residual_ids, tuple(kept), plan.policy, plan.version)

    def distill(self, plan: CivilizationPlan, claims: Sequence[ClaimRecord]) -> ResearchSeed:
        verified: list[
            tuple[str, str, int, int, str, str, str, tuple[str, ...], tuple[str, ...]]
        ] = []
        for claim in claims:
            decision = self.judge_claim(claim)
            if decision.verified:
                verified.append(
                    (
                        claim.claim_id,
                        claim.statement,
                        int(claim.output_status),
                        int(claim.evidence_status),
                        claim.producer_id,
                        claim.falsifier_id,
                        claim.verifier_id,
                        tuple(claim.provenance),
                        tuple(claim.tests),
                    )
                )
        blueprints = tuple(
            (
                unit.unit_id,
                unit.kind.value,
                unit.role,
                unit.depth,
                unit.capabilities,
                unit.parent_id,
            )
            for unit in plan.units
            if unit.materialized
        )
        return ResearchSeed(
            question=plan.question,
            residual_ids=plan.residual_ids,
            unit_blueprints=blueprints,
            verified_claims=tuple(sorted(verified)),
            policy=plan.policy,
            source_plan_hash=plan.digest(),
        )

    @staticmethod
    def regenerate(seed: ResearchSeed) -> CivilizationPlan:
        if not seed.question.strip():
            raise ValueError("invalid seed: question is required")
        units: list[ResearchUnit] = []
        seen: set[str] = set()
        for unit_id, kind, role, depth, capabilities, parent_id in seed.unit_blueprints:
            if unit_id in seen:
                raise ValueError("invalid seed: duplicate unit id")
            seen.add(unit_id)
            units.append(
                ResearchUnit(
                    unit_id=unit_id,
                    kind=ResearchUnitKind(kind),
                    role=role,
                    depth=depth,
                    capabilities=tuple(capabilities),
                    parent_id=parent_id,
                    materialized=True,
                )
            )
        unit_ids = {u.unit_id for u in units}
        for unit in units:
            if unit.parent_id and unit.parent_id not in unit_ids:
                raise ValueError("invalid seed: missing parent blueprint")
            if unit.depth > seed.policy.max_depth:
                raise ValueError("invalid seed: depth exceeds policy")
        required_roles = {u.role for u in units}
        if not ResearchCivilizationKernel._CONTROL_ROLES.issubset(required_roles):
            raise ValueError("invalid seed: missing irreducible scientific control role")
        if len(units) > seed.policy.max_materialized_units:
            raise ValueError("invalid seed: materialization budget exceeded")
        return CivilizationPlan(seed.question, seed.residual_ids, tuple(units), seed.policy, seed.version)

    def regeneration_closure(self, plan: CivilizationPlan, rebuilt: CivilizationPlan) -> float:
        required = (unit.unit_id for unit in plan.materialized_units())
        rebuilt_ids = (unit.unit_id for unit in rebuilt.materialized_units())
        return self.morphogenesis.regeneration_closure(required, rebuilt_ids)
