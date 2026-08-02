from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .materials import default_material_atlas
from .mission import demo_air_mission
from .models import default_air, demo_rotor
from .multifidelity import (
    MultiFidelityPolicy,
    ResourceEnvelope,
    merge_shard_reports,
    plan_shards,
    run_multifidelity_campaign,
)
from .system_optimizer import InfiniteSystemFrontier, SystemSearchConstraints


@dataclass(frozen=True)
class R04OAKGate:
    name: str
    passed: bool
    observation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R04OAKReport:
    status: str
    gates: tuple[R04OAKGate, ...]
    model_class: str = "adaptive-multifidelity-sharded-evidence-campaign"
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


def relaxed_r04_constraints() -> SystemSearchConstraints:
    return SystemSearchConstraints(
        maximum_rotor_mass_kg=None,
        minimum_structural_safety_factor=0.05,
        maximum_overall_spl_db=None,
        minimum_robust_feasible_probability=0.0,
        minimum_safe_continuation_fraction=0.0,
        maximum_expected_shaft_energy_j=None,
        maximum_tip_mach=2.0,
    )


def permissive_r04_policy() -> MultiFidelityPolicy:
    return MultiFidelityPolicy(
        f1_utility_threshold=-1.0,
        f2_score_threshold=-2.0,
    )


def run_r04_benchmarks() -> R04OAKReport:
    rotor = demo_rotor()
    medium = default_air()
    mission = demo_air_mission()
    atlas = default_material_atlas()
    frontier = InfiniteSystemFrontier(namespace="omega-propulsion-r04-oak")
    policy = permissive_r04_policy()
    constraints = relaxed_r04_constraints()
    resources = ResourceEnvelope(max_cost_units=1_000.0, checkpoint_interval=2, shard_count=2)
    campaign_id = "omega-propulsion-r04-oak-campaign"

    full = run_multifidelity_campaign(
        rotor,
        medium,
        mission,
        campaign_id=campaign_id,
        start_index=0,
        count=4,
        resources=resources,
        frontier=frontier,
        atlas=atlas,
        constraints=constraints,
        policy=policy,
    )
    left = run_multifidelity_campaign(
        rotor,
        medium,
        mission,
        campaign_id=campaign_id,
        start_index=0,
        count=2,
        resources=resources,
        frontier=frontier,
        atlas=atlas,
        constraints=constraints,
        policy=policy,
    )
    right = run_multifidelity_campaign(
        rotor,
        medium,
        mission,
        campaign_id=campaign_id,
        start_index=2,
        count=2,
        resources=resources,
        frontier=frontier,
        atlas=atlas,
        constraints=constraints,
        policy=policy,
    )
    merged = merge_shard_reports((right, left), campaign_id=campaign_id)
    manifests = plan_shards(campaign_id=campaign_id, start_index=0, count=11, shard_count=3)
    low_budget = run_multifidelity_campaign(
        rotor,
        medium,
        mission,
        campaign_id="omega-propulsion-r04-backpressure",
        start_index=100,
        count=5,
        resources=ResourceEnvelope(max_cost_units=2.0, checkpoint_interval=1),
        frontier=frontier,
        atlas=atlas,
        constraints=constraints,
        policy=policy,
    )
    strict = run_multifidelity_campaign(
        rotor,
        medium,
        mission,
        campaign_id="omega-propulsion-r04-mminus",
        start_index=0,
        count=3,
        resources=ResourceEnvelope(max_cost_units=20.0, checkpoint_interval=1),
        frontier=frontier,
        atlas=atlas,
        constraints=SystemSearchConstraints(
            maximum_rotor_mass_kg=0.01,
            minimum_structural_safety_factor=1.5,
            maximum_overall_spl_db=80.0,
            minimum_robust_feasible_probability=1.0,
            minimum_safe_continuation_fraction=1.0,
            maximum_tip_mach=0.40,
        ),
        policy=policy,
    )

    covered = [
        index
        for manifest in manifests
        for index in range(manifest.start_index, manifest.end_index_exclusive)
    ]
    gates = (
        R04OAKGate(
            "fidelity-labels-deny-physical-certification",
            all(
                not stage.physical_fidelity_claim
                for stage in (policy.f0, policy.f1, policy.f2)
            ),
            "F0/F1/F2 are evidence-depth labels; F2 is not CFD or experiment",
        ),
        R04OAKGate(
            "adaptive-three-stage-campaign",
            full.f0_count == 4 and full.f1_count > 0 and full.f2_count > 0,
            f"F0={full.f0_count}, F1={full.f1_count}, F2={full.f2_count}",
        ),
        R04OAKGate(
            "resource-envelope-respected",
            full.consumed_cost_units <= resources.max_cost_units,
            f"cost={full.consumed_cost_units}/{resources.max_cost_units}",
        ),
        R04OAKGate(
            "backpressure-stops-before-overrun",
            low_budget.consumed_cost_units <= 2.0
            and low_budget.f0_count < low_budget.requested_count
            and "resource_budget" in low_budget.backpressure.stop_reason,
            (
                f"admitted={low_budget.f0_count}/{low_budget.requested_count}, "
                f"cost={low_budget.consumed_cost_units}"
            ),
        ),
        R04OAKGate(
            "shard-plan-exact-cover",
            covered == list(range(11))
            and len(covered) == len(set(covered))
            and sum(item.count for item in manifests) == 11,
            f"shards={[(item.start_index, item.count) for item in manifests]}",
        ),
        R04OAKGate(
            "shard-merge-equals-unsharded-chain",
            merged.final_chain_digest == full.final_chain_digest
            and merged.evaluated_count == full.f0_count,
            (
                f"full={full.final_chain_digest[:16]}..., "
                f"merged={merged.final_chain_digest[:16]}..."
            ),
        ),
        R04OAKGate(
            "negative-memory-retained",
            len(strict.m_minus) > 0
            and all("do not convert" in item.action for item in strict.m_minus),
            f"m_minus_records={len(strict.m_minus)}",
        ),
        R04OAKGate(
            "candidate-local-promotion-policy",
            policy.preserve_candidate_local_decisions
            and all(item.candidate_id for item in full.promotions),
            f"promotion_decisions={len(full.promotions)}",
        ),
        R04OAKGate(
            "checkpoints-and-hash-chain",
            len(full.final_chain_digest) == 64
            and all(
                left.next_index < right.next_index
                for left, right in zip(full.checkpoints, full.checkpoints[1:])
            ),
            f"checkpoints={[item.next_index for item in full.checkpoints]}",
        ),
        R04OAKGate(
            "frontier-remains-unbounded",
            full.permanent_total_cap is None
            and full.frontier.to_dict()["permanent_total_cap"] is None
            and frontier.vector_at(10_000_000, atlas).frontier_index == 10_000_000,
            "no permanent total cardinality is encoded",
        ),
        R04OAKGate(
            "not-physics-certified",
            not full.physics_certified and not merged.physics_certified,
            "adaptive campaign remains computational screening evidence",
        ),
    )
    passed = all(gate.passed for gate in gates)
    return R04OAKReport(
        status=(
            "CERTIFIED_COMPUTATIONAL_ADAPTIVE_MULTIFIDELITY_R0_4"
            if passed
            else "FAILED_OAK_GATES"
        ),
        gates=gates,
    )
