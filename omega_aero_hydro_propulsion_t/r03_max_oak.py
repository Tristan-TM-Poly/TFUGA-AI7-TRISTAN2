from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .materials import default_material_atlas
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .system_optimizer import InfiniteSystemFrontier, SystemSearchConstraints, evaluate_system_candidate, run_system_campaign


@dataclass(frozen=True)
class MaxOAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R03MaxOAKReport:
    status: str
    gates: tuple[MaxOAKGate, ...]
    model_class: str = "unbounded-stream-system-search-structural-robust-acoustic-fault"
    physics_certified: bool = False

    @property
    def passed(self) -> bool:
        return all(gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "model_class": self.model_class,
            "physics_certified": self.physics_certified,
            "gates": [gate.to_dict() for gate in self.gates],
        }


def _relaxed_constraints() -> SystemSearchConstraints:
    return SystemSearchConstraints(
        maximum_rotor_mass_kg=None,
        minimum_structural_safety_factor=0.05,
        maximum_overall_spl_db=None,
        minimum_robust_feasible_probability=0.0,
        minimum_safe_continuation_fraction=0.0,
        maximum_expected_shaft_energy_j=None,
        maximum_tip_mach=2.0,
    )


def run_r03_max_benchmarks() -> R03MaxOAKReport:
    rotor = demo_rotor()
    medium = default_air()
    mission = demo_air_mission()
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier()
    constraints = _relaxed_constraints()

    vector_a = frontier.vector_at(42, atlas)
    vector_b = frontier.vector_at(42, atlas)
    very_far = frontier.vector_at(1_000_000, atlas)
    candidate = evaluate_system_candidate(rotor, medium, mission, vector_a, atlas=atlas, constraints=constraints)
    full = run_system_campaign(
        rotor, medium, mission, start_index=0, count=6, frontier=frontier,
        atlas=atlas, constraints=constraints, checkpoint_interval=2,
    )
    first = run_system_campaign(
        rotor, medium, mission, start_index=0, count=3, frontier=frontier,
        atlas=atlas, constraints=constraints, checkpoint_interval=2,
    )
    second = run_system_campaign(
        rotor, medium, mission, start_index=3, count=3, frontier=frontier,
        atlas=atlas, constraints=constraints, checkpoint_interval=2,
        previous_chain_digest=first.final_chain_digest,
    )
    ids = [item.vector.candidate_id for item in full.candidates]

    gates = (
        MaxOAKGate(
            "material-atlas-provenance",
            len(atlas.names) >= 5 and all(not atlas.get_record(name).engineering_allowables for name in atlas.names),
            f"materials={len(atlas.names)}, engineering_allowables=false",
        ),
        MaxOAKGate("frontier-deterministic", vector_a == vector_b, f"candidate_id={vector_a.candidate_id}"),
        MaxOAKGate(
            "frontier-no-fixed-total-cap",
            frontier.to_dict()["permanent_total_cap"] is None and very_far.frontier_index == 1_000_000,
            f"far_candidate={very_far.candidate_id}",
        ),
        MaxOAKGate(
            "candidate-evidence-hash",
            len(candidate.evidence_hash) == 64 and not candidate.physics_certified,
            f"hash={candidate.evidence_hash[:16]}..., certified={candidate.physics_certified}",
        ),
        MaxOAKGate(
            "campaign-count-exact",
            full.evaluated_count == 6 and full.next_index == 6,
            f"evaluated={full.evaluated_count}, next={full.next_index}",
        ),
        MaxOAKGate("campaign-ids-unique", len(ids) == len(set(ids)), f"unique={len(set(ids))}/{len(ids)}"),
        MaxOAKGate(
            "campaign-resume-hash-chain",
            second.final_chain_digest == full.final_chain_digest,
            f"full={full.final_chain_digest[:16]}..., resumed={second.final_chain_digest[:16]}...",
        ),
        MaxOAKGate(
            "pareto-and-ranking-produced",
            full.best is not None and len(full.pareto_front) > 0,
            f"feasible={full.feasible_count}, pareto={len(full.pareto_front)}",
        ),
        MaxOAKGate(
            "checkpoint-monotonicity",
            all(left.next_index < right.next_index for left, right in zip(full.checkpoints, full.checkpoints[1:])),
            f"checkpoints={[item.next_index for item in full.checkpoints]}",
        ),
        MaxOAKGate("not-physics-certified", not full.physics_certified, "system search remains computational screening evidence"),
    )
    passed = all(gate.passed for gate in gates)
    return R03MaxOAKReport(
        status="CERTIFIED_COMPUTATIONAL_SYSTEM_SEARCH_R0_3_MAX" if passed else "FAILED_OAK_GATES",
        gates=gates,
    )
