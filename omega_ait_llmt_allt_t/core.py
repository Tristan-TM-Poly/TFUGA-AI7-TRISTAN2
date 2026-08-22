from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json


HARD_GATES = (
    "truth",
    "safety",
    "authority",
    "provenance",
    "independent_verification",
    "rollback",
    "observability",
)

TOPOLOGY_ORDER = ("NO_ACTION", "GO_MIN", "AIT", "LLMT", "ALLT")


@dataclass(frozen=True)
class MissionIR:
    mission_id: str
    residual: float
    complexity: int
    uncertainty: float
    risk: float
    required_capabilities: tuple[str, ...] = ()
    evidence_count: int = 1
    truth_ok: bool = True
    safety_ok: bool = True
    authority_ok: bool = True
    provenance_ok: bool = True
    independent_verification_ok: bool = True
    rollback_ok: bool = True
    observability_ok: bool = True

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise ValueError("mission_id is required")
        if not 0.0 <= self.residual <= 1.0:
            raise ValueError("residual must be in [0, 1]")
        if not 0 <= self.complexity <= 100:
            raise ValueError("complexity must be in [0, 100]")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0, 1]")
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("risk must be in [0, 1]")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be non-negative")


@dataclass(frozen=True)
class IntelligenceGenome:
    genome_id: str
    primitives: tuple[str, ...]
    topology_pool: tuple[str, ...]
    max_meta_depth: int = 2
    authority_policy: str = "review_only"


@dataclass(frozen=True)
class MutationReceipt:
    mutation_id: str
    parent_genome_id: str
    status: str
    hypothesis: str
    candidate_primitives: tuple[str, ...]
    verified_gain: float
    auto_promotion: bool
    rollback_available: bool


def default_genome() -> IntelligenceGenome:
    return IntelligenceGenome(
        genome_id="omega-ait-llmt-allt-r01",
        primitives=(
            "OBSERVE",
            "RESIDUALIZE",
            "QUESTION",
            "REPRESENT",
            "GENERATE",
            "COMPOSE",
            "EXECUTE",
            "VERIFY",
            "COUNTERFACTUALIZE",
            "SELECT",
            "DISTILL",
            "PRUNE",
            "REGENERATE",
            "META_VERIFY",
        ),
        topology_pool=TOPOLOGY_ORDER,
        max_meta_depth=2,
        authority_policy="review_only",
    )


def _gate_map(mission: MissionIR) -> dict[str, bool]:
    return {
        "truth": mission.truth_ok,
        "safety": mission.safety_ok,
        "authority": mission.authority_ok,
        "provenance": mission.provenance_ok,
        "independent_verification": mission.independent_verification_ok,
        "rollback": mission.rollback_ok,
        "observability": mission.observability_ok,
    }


def _representation(mission: MissionIR) -> str:
    caps = set(mission.required_capabilities)
    if "simulation" in caps:
        return "simulation"
    if mission.uncertainty >= 0.65:
        return "evidence_graph"
    if mission.complexity >= 70 or len(caps) >= 6:
        return "hypergraph"
    if "formal_proof" in caps or "code" in caps:
        return "program_ir"
    return "structured_text"


def _score(mission: MissionIR) -> float:
    capability_pressure = 4.0 * max(0, len(set(mission.required_capabilities)) - 1)
    return float(mission.complexity) + 30.0 * mission.uncertainty + 30.0 * mission.risk + capability_pressure


def _topology_for_score(score: float) -> str:
    if score < 25:
        return "GO_MIN"
    if score < 45:
        return "AIT"
    if score < 70:
        return "LLMT"
    return "ALLT"


def compile_mission(mission: MissionIR, genome: IntelligenceGenome | None = None) -> dict:
    """Compile a mission into a proof-carrying architecture proposal.

    R0.1 is a deterministic planning/judiciary kernel. It never performs
    external actions and never auto-promotes generated architectures.
    """
    genome = genome or default_genome()
    gates = _gate_map(mission)
    failed = [name for name in HARD_GATES if not gates[name]]
    rationale: list[str] = []

    if failed:
        topology = "NO_ACTION"
        status = "BLOCKED"
        rationale.append("One or more non-compensatory OAK gates failed.")
    elif mission.residual <= 0.05:
        topology = "NO_ACTION"
        status = "NO_ACTION"
        rationale.append("Residual is below the action threshold.")
    elif mission.evidence_count == 0 and mission.uncertainty >= 0.40:
        topology = "GO_MIN"
        status = "ABSTAIN_MORE_EVIDENCE"
        rationale.append("Evidence is insufficient for the current uncertainty.")
    else:
        score = _score(mission)
        topology = _topology_for_score(score)
        status = "CANDIDATE_FOR_REVIEW"
        rationale.append(f"Topology selected from deterministic pressure score {score:.2f}.")

    capability_count = 0 if topology == "NO_ACTION" else max(1, len(set(mission.required_capabilities)))
    return {
        "schema_version": "omega-ait-llmt-allt-plan-r01",
        "plan_id": f"plan:{mission.mission_id}",
        "mission_id": mission.mission_id,
        "status": status,
        "topology": topology,
        "representation": _representation(mission),
        "capability_count": capability_count,
        "required_capabilities": sorted(set(mission.required_capabilities)),
        "hard_gates": gates,
        "failed_gates": failed,
        "authority": genome.authority_policy,
        "max_meta_depth": genome.max_meta_depth,
        "auto_promotion": False,
        "external_action_performed": False,
        "rationale": rationale,
    }


def mutate_genome(genome: IntelligenceGenome, *, residual_signal: str, verified_gain: float) -> MutationReceipt:
    """Generate a candidate genome mutation without promoting it."""
    signal = residual_signal.strip().upper().replace(" ", "_") or "UNKNOWN_RESIDUAL"
    primitive = f"PROBE_{signal}"
    candidate = tuple(dict.fromkeys((*genome.primitives, primitive)))
    status = "CANDIDATE" if verified_gain > 0 else "REJECTED_NO_VERIFIED_GAIN"
    material = f"{genome.genome_id}|{signal}|{verified_gain:.12g}".encode()
    mutation_id = f"mutation:{sha256(material).hexdigest()[:16]}"
    return MutationReceipt(
        mutation_id=mutation_id,
        parent_genome_id=genome.genome_id,
        status=status,
        hypothesis=f"Adding {primitive} may reduce residual {signal}.",
        candidate_primitives=candidate,
        verified_gain=float(verified_gain),
        auto_promotion=False,
        rollback_available=True,
    )


def constitution() -> dict:
    return {
        "schema_version": "omega-ait-llmt-allt-constitution-r01",
        "authority": "review_only",
        "hard_gates": list(HARD_GATES),
        "hard_gates_are_non_compensatory": True,
        "generator_is_judge": False,
        "capability_implies_authority": False,
        "automation_implies_permission": False,
        "simulation_is_reality": False,
        "automatic_promotion_allowed": False,
        "external_action_surface": False,
        "meta_depth_requires_verified_gain": True,
        "no_zero_touch_without_observability": True,
        "ablation_required_for_promotion": True,
    }


def regeneration_receipt(genome: IntelligenceGenome | None = None) -> dict:
    genome = genome or default_genome()
    seed = {"genome": asdict(genome), "constitution": constitution()}
    canonical = json.dumps(seed, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "omega-ait-llmt-allt-regeneration-r01",
        "seed_sha256": sha256(canonical).hexdigest(),
        "regeneration_level": "R0.1_SEED",
        "deterministic_seed": True,
        "full_R5_self_hosting_proven": False,
        "rollback_available": True,
    }


def demo_cases() -> list[MissionIR]:
    return [
        MissionIR(mission_id="simple.min", residual=0.30, complexity=8, uncertainty=0.10, risk=0.05, required_capabilities=("reasoning",)),
        MissionIR(mission_id="research.fertile", residual=0.85, complexity=55, uncertainty=0.75, risk=0.25, required_capabilities=("search", "simulation", "verification"), evidence_count=0),
        MissionIR(mission_id="crossdomain.complex", residual=0.90, complexity=88, uncertainty=0.55, risk=0.35, required_capabilities=("physics", "code", "simulation", "search", "verification", "counterfactual")),
        MissionIR(mission_id="authority.blocked", residual=0.95, complexity=90, uncertainty=0.20, risk=0.90, required_capabilities=("external_action", "planning"), authority_ok=False),
    ]


def demo_bundle() -> dict:
    genome = default_genome()
    return {
        "schema_version": "omega-ait-llmt-allt-demo-r01",
        "reports": [compile_mission(case, genome) for case in demo_cases()],
        "mutation": asdict(mutate_genome(genome, residual_signal="representation fragility", verified_gain=0.10)),
        "regeneration": regeneration_receipt(genome),
    }
