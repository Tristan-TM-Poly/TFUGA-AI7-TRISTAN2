from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from itertools import combinations
import json
from typing import Iterable, Sequence


CONSTITUTION = (
    "Generated != Verified",
    "Generator != Judge",
    "SelfModification != SelfApproval",
    "ToolAvailable != ToolNecessary",
    "Capability != Authority",
    "MoreSkills != MoreCapability",
    "MoreMeta != Better",
    "PersistentStructure <= VerifiedNecessaryStructure",
)


def _norm_caps(values: Iterable[str]) -> frozenset[str]:
    return frozenset(str(value).strip() for value in values if str(value).strip())


@dataclass(frozen=True)
class SkillGenome:
    name: str
    capabilities: frozenset[str]
    verified: bool = False
    evidence_refs: tuple[str, ...] = ()
    permissions: frozenset[str] = frozenset()
    cost: float = 1.0
    risk: float = 0.0
    complexity: float = 0.0
    transfer: float = 1.0
    regenerability: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", _norm_caps(self.capabilities))
        object.__setattr__(self, "permissions", _norm_caps(self.permissions))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))
        if not self.name.strip():
            raise ValueError("skill name is required")
        for field_name in ("cost", "risk", "complexity"):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")
        for field_name in ("transfer", "regenerability"):
            value = getattr(self, field_name)
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be in [0,1]")


@dataclass(frozen=True)
class SkillPlan:
    mode: str
    skills: tuple[str, ...]
    coverage: frozenset[str]
    residuals: frozenset[str]
    verified: bool
    cost: float
    risk: float
    complexity: float
    transfer: float
    regenerability: float
    auto_promote: bool = False
    external_action_performed: bool = False

    @property
    def sufficient(self) -> bool:
        return not self.residuals


@dataclass(frozen=True)
class MetaImprovementReceipt:
    accepted: bool
    generator: str
    judge: str
    verified_gain: float
    complexity_debt: float
    risk_debt: float
    meta_debt: float
    independent_evidence: bool
    reasons: tuple[str, ...]
    auto_promoted: bool = False


@dataclass(frozen=True)
class SkillCrystal:
    name: str
    capabilities: tuple[str, ...]
    source_skills: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    kernel_ops: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class CrystallizationReceipt:
    status: str
    reasons: tuple[str, ...]
    crystal: SkillCrystal | None
    auto_promoted: bool = False


@dataclass(frozen=True)
class RegenerationSeed:
    crystal_digest: str
    required_capabilities: tuple[str, ...]
    kernel_ops: tuple[str, ...]
    seed_digest: str


def meta_generalize(skills: Sequence[SkillGenome]) -> dict:
    verified = [skill for skill in skills if skill.verified and skill.evidence_refs]
    if not verified:
        return {
            "candidate_invariants": [],
            "support": 0,
            "status": "HOLD",
            "note": "No evidence-bearing verified skills; no meta-generalization promoted.",
        }
    common = set(verified[0].capabilities)
    for skill in verified[1:]:
        common.intersection_update(skill.capabilities)
    return {
        "candidate_invariants": sorted(common),
        "support": len(verified),
        "status": "CANDIDATE",
        "note": "Cross-skill invariant candidate only; not a universal law.",
    }


def _make_plan(mode: str, selected: Sequence[SkillGenome], required: frozenset[str]) -> SkillPlan:
    coverage = frozenset().union(*(skill.capabilities for skill in selected)) if selected else frozenset()
    residuals = required - coverage
    evidence_bearing = all(skill.verified and skill.evidence_refs for skill in selected) if selected else False
    return SkillPlan(
        mode=mode,
        skills=tuple(sorted(skill.name for skill in selected)),
        coverage=coverage & required,
        residuals=residuals,
        verified=evidence_bearing and not residuals,
        cost=sum(skill.cost for skill in selected),
        risk=sum(skill.risk for skill in selected),
        complexity=sum(skill.complexity for skill in selected),
        transfer=min((skill.transfer for skill in selected), default=0.0),
        regenerability=min((skill.regenerability for skill in selected), default=0.0),
    )


def compile_counterfactual_plans(
    required_capabilities: Iterable[str],
    skills: Sequence[SkillGenome],
    *,
    max_combo: int = 3,
) -> tuple[SkillPlan, ...]:
    required = _norm_caps(required_capabilities)
    plans: list[SkillPlan] = [
        SkillPlan(
            mode="NO_ACTION",
            skills=(),
            coverage=frozenset(),
            residuals=required,
            verified=not required,
            cost=0.0,
            risk=0.0,
            complexity=0.0,
            transfer=0.0,
            regenerability=1.0,
        )
    ]

    for skill in skills:
        plans.append(_make_plan("REUSE", [skill], required))

    limit = min(max_combo, len(skills))
    for size in range(2, limit + 1):
        for combo in combinations(skills, size):
            plans.append(_make_plan("COMPOSE", combo, required))

    existing_coverage = frozenset().union(*(skill.capabilities for skill in skills)) if skills else frozenset()
    residuals = required - existing_coverage
    if residuals:
        plans.append(
            SkillPlan(
                mode="GENERATE_RESIDUAL",
                skills=(),
                coverage=existing_coverage & required,
                residuals=residuals,
                verified=False,
                cost=0.0,
                risk=0.0,
                complexity=float(len(residuals)),
                transfer=0.0,
                regenerability=0.0,
            )
        )

    unique: dict[tuple[str, tuple[str, ...], tuple[str, ...]], SkillPlan] = {}
    for plan in plans:
        key = (plan.mode, plan.skills, tuple(sorted(plan.residuals)))
        unique[key] = plan
    return tuple(unique.values())


def select_minimum_sufficient_plan(plans: Sequence[SkillPlan]) -> SkillPlan | None:
    eligible = [plan for plan in plans if plan.sufficient and plan.verified]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda plan: (
            plan.cost + plan.risk + plan.complexity,
            len(plan.skills),
            -plan.regenerability,
            plan.skills,
        ),
    )


def generate_residual_skill_candidates(
    required_capabilities: Iterable[str],
    skills: Sequence[SkillGenome],
) -> tuple[dict, ...]:
    required = _norm_caps(required_capabilities)
    covered = frozenset().union(*(skill.capabilities for skill in skills)) if skills else frozenset()
    residuals = sorted(required - covered)
    return tuple(
        {
            "name": f"candidate-{capability.lower().replace(' ', '-')}",
            "capability": capability,
            "status": "CANDIDATE",
            "auto_promote": False,
            "required_gates": (
                "SkillSpec",
                "trust review",
                "positive/negative/incomplete/adversarial evals",
                "behavioral evidence",
                "independent judge",
            ),
        }
        for capability in residuals
    )


def ablation_report(
    plan: SkillPlan,
    skill_index: dict[str, SkillGenome],
    required_capabilities: Iterable[str],
) -> dict:
    required = _norm_caps(required_capabilities)
    redundant: list[str] = []
    indispensable: list[str] = []
    for name in plan.skills:
        remaining = [skill_index[item] for item in plan.skills if item != name]
        coverage = frozenset().union(*(skill.capabilities for skill in remaining)) if remaining else frozenset()
        if required <= coverage:
            redundant.append(name)
        else:
            indispensable.append(name)
    return {
        "redundant_candidates": sorted(redundant),
        "indispensable": sorted(indispensable),
        "automatic_deletion_authorized": False,
    }


def evaluate_meta_improvement(
    *,
    generator: str,
    judge: str,
    verified_gain: float,
    complexity_debt: float,
    risk_debt: float,
    meta_debt: float,
    independent_evidence: bool,
) -> MetaImprovementReceipt:
    reasons: list[str] = []
    if generator == judge:
        reasons.append("generator_judge_collision")
    if not independent_evidence:
        reasons.append("independent_evidence_missing")
    rent = complexity_debt + risk_debt + meta_debt
    if verified_gain <= rent:
        reasons.append("meta_complexity_rent_not_paid")
    return MetaImprovementReceipt(
        accepted=not reasons,
        generator=generator,
        judge=judge,
        verified_gain=verified_gain,
        complexity_debt=complexity_debt,
        risk_debt=risk_debt,
        meta_debt=meta_debt,
        independent_evidence=independent_evidence,
        reasons=tuple(reasons),
    )


def meta_depth_decision(
    *,
    verified_gain: float,
    extra_complexity: float,
    compute_cost: float,
    risk: float,
    meta_debt: float,
    threshold: float = 1.0,
) -> dict:
    denominator = extra_complexity + compute_cost + risk + meta_debt
    ratio = float("inf") if denominator == 0 and verified_gain > 0 else (
        0.0 if denominator == 0 else verified_gain / denominator
    )
    return {
        "continue": verified_gain > 0 and ratio > threshold,
        "ratio": ratio,
        "threshold": threshold,
        "rule": "increase meta depth only when verified gain pays added complexity/compute/risk/meta debt",
    }


def crystallize_skill_plan(
    *,
    name: str,
    plan: SkillPlan,
    skill_index: dict[str, SkillGenome],
    generator: str,
    judge: str,
    independent_evidence: bool,
    tests_passed: bool,
    kernel_ops: Iterable[str] = (
        "INTENT",
        "RESIDUALIZE",
        "SEARCH",
        "COMPOSE",
        "GENERATE",
        "VERIFY",
        "ABLATE",
        "REGENERATE",
    ),
) -> CrystallizationReceipt:
    reasons: list[str] = []
    if not plan.sufficient or not plan.verified:
        reasons.append("plan_not_verified_sufficient")
    if generator == judge:
        reasons.append("generator_judge_collision")
    if not independent_evidence:
        reasons.append("independent_evidence_missing")
    if not tests_passed:
        reasons.append("tests_not_passed")

    evidence_refs = tuple(
        sorted(
            {
                evidence
                for skill_name in plan.skills
                for evidence in skill_index[skill_name].evidence_refs
            }
        )
    )
    if not evidence_refs:
        reasons.append("evidence_refs_missing")

    if reasons:
        return CrystallizationReceipt(status="HOLD", reasons=tuple(reasons), crystal=None)

    payload = {
        "name": name,
        "capabilities": sorted(plan.coverage),
        "source_skills": sorted(plan.skills),
        "evidence_refs": evidence_refs,
        "kernel_ops": tuple(kernel_ops),
    }
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    crystal = SkillCrystal(
        name=name,
        capabilities=tuple(payload["capabilities"]),
        source_skills=tuple(payload["source_skills"]),
        evidence_refs=evidence_refs,
        kernel_ops=tuple(payload["kernel_ops"]),
        digest=digest,
    )
    return CrystallizationReceipt(status="CANDIDATE_CRYSTAL", reasons=(), crystal=crystal)


def regeneration_seed(crystal: SkillCrystal) -> RegenerationSeed:
    payload = {
        "crystal_digest": crystal.digest,
        "required_capabilities": crystal.capabilities,
        "kernel_ops": crystal.kernel_ops,
    }
    seed_digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return RegenerationSeed(
        crystal_digest=crystal.digest,
        required_capabilities=crystal.capabilities,
        kernel_ops=crystal.kernel_ops,
        seed_digest=seed_digest,
    )


def regeneration_closure(
    required_capabilities: Iterable[str],
    regenerated_capabilities: Iterable[str],
) -> float:
    required = _norm_caps(required_capabilities)
    if not required:
        return 1.0
    regenerated = _norm_caps(regenerated_capabilities)
    return len(required & regenerated) / len(required)


def receipt_to_dict(receipt: object) -> dict:
    return asdict(receipt)
