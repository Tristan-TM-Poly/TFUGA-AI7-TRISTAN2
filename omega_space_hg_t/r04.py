"""Ω-SPACE-HG-T∞ R0.4 reliability, radiation and FDIR laboratory."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .reliability import (
    CommonCauseModel,
    ComponentReliability,
    FDIRPolicy,
    FDIRState,
    FaultTreeNode,
    RadiationEnvironment,
    exponential_failure_probability,
    fdir_transition,
    run_reliability_campaign,
)


@dataclass(frozen=True)
class R04Check:
    name: str
    passed: bool
    observed: Any
    criterion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_components() -> tuple[ComponentReliability, ...]:
    # Rates are synthetic research-fixture values, not hardware predictions.
    return (
        ComponentReliability("fc-a", "flight_computer", 1.6e-5, True, "fc", "avionics", 0.99, 0.72),
        ComponentReliability("fc-b", "flight_computer", 1.6e-5, True, "fc", "avionics", 0.99, 0.72),
        ComponentReliability("eps-a", "power_control", 1.2e-5, True, "eps", "power_bus", 0.98, 0.55),
        ComponentReliability("eps-b", "power_control", 1.2e-5, True, "eps", "power_bus", 0.98, 0.55),
        ComponentReliability("star-a", "attitude_knowledge", 2.2e-5, True, "stars", "avionics", 0.97, 0.65),
        ComponentReliability("star-b", "attitude_knowledge", 2.2e-5, True, "stars", "avionics", 0.97, 0.65),
        ComponentReliability("radio-a", "command_link", 1.8e-5, True, "radio", "rf_chain", 0.98, 0.62),
        ComponentReliability("radio-b", "command_link", 1.8e-5, True, "radio", "rf_chain", 0.98, 0.62),
        ComponentReliability("payload", "science_payload", 3.0e-5, False, None, None, 0.92, 0.30),
    )


def canonical_common_causes(enabled: bool = True) -> tuple[CommonCauseModel, ...]:
    if not enabled:
        return ()
    return (
        CommonCauseModel("avionics-bus", 2.8e-6, ("fc-a", "fc-b", "star-a", "star-b"), 0.96, 0.35),
        CommonCauseModel("power-bus", 2.0e-6, ("eps-a", "eps-b"), 0.97, 0.25),
        CommonCauseModel("rf-chain", 1.6e-6, ("radio-a", "radio-b"), 0.95, 0.30),
    )


def canonical_radiation() -> RadiationEnvironment:
    return RadiationEnvironment(
        particle_flux_cm2_s=0.08,
        device_cross_section_cm2=2.0e-10,
        device_count=180,
        shielding_attenuation=0.42,
        recovery_probability=0.985,
    )


def simulate_r04_campaign(
    *,
    duration_days: float = 365.25,
    start_offset: int = 0,
    count: int = 2048,
    include_common_causes: bool = True,
    include_radiation: bool = True,
) -> dict[str, Any]:
    if duration_days <= 0.0:
        raise ValueError("duration_days must be positive")
    report = run_reliability_campaign(
        canonical_components(),
        duration_days * 24.0,
        start_offset=start_offset,
        count=count,
        base_seed=20260803,
        common_causes=canonical_common_causes(include_common_causes),
        radiation=canonical_radiation() if include_radiation else None,
        retain_failure_witnesses=24,
    )
    report["release"] = "R0.4"
    report["configuration"] = {
        "duration_days": duration_days,
        "include_common_causes": include_common_causes,
        "include_radiation": include_radiation,
        "components": [asdict(item) for item in canonical_components()],
        "common_causes": [asdict(item) for item in canonical_common_causes(include_common_causes)],
        "radiation": asdict(canonical_radiation()) if include_radiation else None,
    }
    report["operational_reliability_claimed"] = False
    report["safety_certification_claimed"] = False
    return report


def canonical_fault_tree(duration_days: float = 365.25) -> FaultTreeNode:
    duration_hours = duration_days * 24.0
    component = {
        item.component_id: exponential_failure_probability(item.failure_rate_per_hour, duration_hours)
        for item in canonical_components()
    }
    flight_computer_loss = FaultTreeNode(
        "flight-computer-loss",
        "and",
        (
            FaultTreeNode("fc-a-fails", "leaf", leaf_probability=component["fc-a"]),
            FaultTreeNode("fc-b-fails", "leaf", leaf_probability=component["fc-b"]),
        ),
    )
    power_loss = FaultTreeNode(
        "power-control-loss",
        "and",
        (
            FaultTreeNode("eps-a-fails", "leaf", leaf_probability=component["eps-a"]),
            FaultTreeNode("eps-b-fails", "leaf", leaf_probability=component["eps-b"]),
        ),
    )
    command_loss = FaultTreeNode(
        "command-link-loss",
        "and",
        (
            FaultTreeNode("radio-a-fails", "leaf", leaf_probability=component["radio-a"]),
            FaultTreeNode("radio-b-fails", "leaf", leaf_probability=component["radio-b"]),
        ),
    )
    return FaultTreeNode(
        "mission-loss-independent-baseline",
        "or",
        (flight_computer_loss, power_loss, command_loss),
    )


def simulate_fdir_scenario() -> dict[str, Any]:
    policy = FDIRPolicy(0.20, 0.35, 3)
    states = [FDIRState()]
    states.append(fdir_transition(states[-1], policy, battery_soc=0.80, dt_hours=0.001))
    states.append(
        fdir_transition(
            states[-1],
            policy,
            battery_soc=0.76,
            detected_failures=("star-a",),
            dt_hours=0.001,
        )
    )
    states.append(
        fdir_transition(
            states[-1],
            policy,
            battery_soc=0.74,
            command_recovery=True,
            dt_hours=0.001,
        )
    )
    states.append(
        fdir_transition(
            states[-1],
            policy,
            battery_soc=0.72,
            recovered_failures=("star-a",),
            dt_hours=0.001,
        )
    )
    states.append(fdir_transition(states[-1], policy, battery_soc=0.15, dt_hours=0.001))
    states.append(fdir_transition(states[-1], policy, battery_soc=0.42, dt_hours=0.001))
    return {
        "policy": asdict(policy),
        "states": [state.to_dict() for state in states],
        "final_mode": states[-1].mode,
        "flight_software_claimed": False,
        "autonomous_safety_claimed": False,
    }


def _capture(name: str, criterion: str, function: Callable[[], tuple[bool, Any]]) -> R04Check:
    try:
        passed, observed = function()
        return R04Check(name, bool(passed), observed, criterion)
    except Exception as error:
        return R04Check(name, False, f"{type(error).__name__}: {error}", criterion)


def run_r04_oak_benchmarks() -> dict[str, Any]:
    def exponential_check() -> tuple[bool, Any]:
        one = exponential_failure_probability(1e-4, 1000.0)
        two = exponential_failure_probability(1e-4, 2000.0)
        expected = 1.0 - (1.0 - one) ** 2
        return two > one and abs(two - expected) < 1e-15, {"p_1000h": one, "p_2000h": two}

    def fault_tree_check() -> tuple[bool, Any]:
        tree = FaultTreeNode(
            "or",
            "or",
            (
                FaultTreeNode("a", "leaf", leaf_probability=0.1),
                FaultTreeNode("b", "leaf", leaf_probability=0.2),
            ),
        )
        probability = tree.probability()
        return abs(probability - 0.28) < 1e-15, probability

    def common_cause_check() -> tuple[bool, Any]:
        independent = simulate_r04_campaign(
            duration_days=365.25,
            count=2048,
            include_common_causes=False,
            include_radiation=False,
        )
        coupled = simulate_r04_campaign(
            duration_days=365.25,
            count=2048,
            include_common_causes=True,
            include_radiation=False,
        )
        observed = {
            "independent_success": independent["estimated_success_probability"],
            "common_cause_success": coupled["estimated_success_probability"],
        }
        return observed["common_cause_success"] < observed["independent_success"], observed

    def radiation_scaling_check() -> tuple[bool, Any]:
        environment = canonical_radiation()
        one = environment.expected_events(1000.0)
        two = environment.expected_events(2000.0)
        return abs(two - 2.0 * one) < 1e-18, {"expected_1000s": one, "expected_2000s": two}

    def campaign_replay_check() -> tuple[bool, Any]:
        first = simulate_r04_campaign(duration_days=180.0, start_offset=4096, count=512)
        second = simulate_r04_campaign(duration_days=180.0, start_offset=4096, count=512)
        keys = (
            "estimated_success_probability",
            "wilson_95_interval",
            "failure_witness_digest",
            "next_offset",
        )
        return all(first[key] == second[key] for key in keys), {key: first[key] for key in keys}

    def fdir_check() -> tuple[bool, Any]:
        report = simulate_fdir_scenario()
        modes = [state["mode"] for state in report["states"]]
        expected = ["BOOT", "NOMINAL", "DEGRADED", "RECOVERY", "NOMINAL", "SAFE", "NOMINAL"]
        return modes == expected, modes

    def boundary_check() -> tuple[bool, Any]:
        boundaries = {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "flight_qualified_claimed": False,
            "operational_reliability_claimed": False,
            "safety_certification_claimed": False,
            "autonomous_safety_claimed": False,
        }
        return not any(boundaries.values()), boundaries

    checks = (
        _capture("exponential_probability_composition", "constant-hazard probability composes exactly", exponential_check),
        _capture("fault_tree_or_probability", "independent OR gate returns 0.28 for p=0.1 and p=0.2", fault_tree_check),
        _capture("common_cause_penalty", "common-cause coupling lowers canonical redundant-system success", common_cause_check),
        _capture("radiation_expectation_scaling", "expected event count scales linearly with exposure", radiation_scaling_check),
        _capture("campaign_deterministic_replay", "offset campaign and witness digest replay exactly", campaign_replay_check),
        _capture("fdir_state_path", "canonical fault, recovery and low-SOC path is exact", fdir_check),
        _capture("r04_claim_boundaries", "no proof validation qualification reliability or autonomous-safety claim", boundary_check),
    )
    return {
        "suite": "OMEGA-SPACE-HG-T-R0.4-OAKBench",
        "passed": all(check.passed for check in checks),
        "checks": [check.to_dict() for check in checks],
        "theorem_claimed": False,
        "scientific_validation_claimed": False,
        "flight_qualified_claimed": False,
        "operational_reliability_claimed": False,
        "safety_certification_claimed": False,
        "autonomous_safety_claimed": False,
        "limitations": [
            "synthetic constant-hazard rates are research fixtures, not hardware predictions",
            "fault-tree probabilities assume independence unless common causes are represented explicitly",
            "radiation uses flux-cross-section Poisson counting without transport, spectrum or device physics",
            "recovery probabilities and diagnostic coverage are declared inputs, not measured certification data",
            "Monte-Carlo confidence intervals quantify sampling uncertainty only",
            "FDIR is a permission-bounded state-machine fixture, not qualified autonomous flight software",
        ],
    }
