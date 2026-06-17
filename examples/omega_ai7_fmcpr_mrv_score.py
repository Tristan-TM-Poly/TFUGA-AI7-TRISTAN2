"""Omega-AI7-FMCPR-MRV matter recovery and valorization scorer.

Scores a multi-stream AI-7 fractal purification/recovery plant. This is a
roadmap/OAK scorer, not a process simulator or regulatory certification tool.

Run:
    python examples/omega_ai7_fmcpr_mrv_score.py
"""

from __future__ import annotations

from dataclasses import dataclass


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class MRVPoint:
    name: str
    mass_in_kg: float
    mass_out_clean_kg: float
    mass_recovered_kg: float
    mass_waste_kg: float
    target_concentration_in: float
    target_concentration_out: float
    recovered_purity: float
    market_required_purity: float
    recovered_unit_value_per_kg: float
    energy_cost: float
    maintenance_cost: float
    compliance_cost: float
    waste_cost: float
    regeneration_cost: float
    toxicity_input: float
    toxicity_output: float
    raman_snr_gain: float
    fouling_penalty: float


@dataclass(frozen=True)
class MRVScore:
    name: str
    mass_balance_error: float
    purification_efficiency: float
    recovery_efficiency: float
    purity_margin: float
    recovered_value: float
    total_cost: float
    net_value: float
    toxicity_reduction: float
    proof_score: float
    oak_status: str
    decision: str
    total_score: float


def score_mrv(point: MRVPoint) -> MRVScore:
    if point.mass_in_kg <= 0:
        raise ValueError("mass_in_kg must be positive")
    if point.target_concentration_in <= 0:
        raise ValueError("target_concentration_in must be positive")

    mass_accounted = point.mass_out_clean_kg + point.mass_recovered_kg + point.mass_waste_kg
    mass_balance_error = abs(point.mass_in_kg - mass_accounted) / point.mass_in_kg

    purification_eff = (point.target_concentration_in - point.target_concentration_out) / point.target_concentration_in
    target_mass_in = point.mass_in_kg * point.target_concentration_in
    recovery_eff = point.mass_recovered_kg * point.recovered_purity / max(target_mass_in, 1e-12)
    purity_margin = point.recovered_purity - point.market_required_purity

    recovered_value = point.mass_recovered_kg * point.recovered_purity * point.recovered_unit_value_per_kg
    total_cost = (
        point.energy_cost
        + point.maintenance_cost
        + point.compliance_cost
        + point.waste_cost
        + point.regeneration_cost
    )
    net_value = recovered_value - total_cost
    toxicity_reduction = point.toxicity_input - point.toxicity_output

    proof_score = min(
        clamp01(point.raman_snr_gain / 3.0),
        clamp01(1.0 - mass_balance_error),
        clamp01(1.0 - point.fouling_penalty),
    )

    critical_pass = [
        mass_balance_error < 0.05,
        purification_eff > 0.0,
        toxicity_reduction > 0.0,
        point.raman_snr_gain > 1.0,
        point.fouling_penalty < 0.5,
    ]
    value_pass = net_value > 0 and purity_margin >= 0

    if all(critical_pass) and value_pass:
        oak = "VALIDATED_PROXY_VALORIZABLE"
        decision = "valorize"
    elif all(critical_pass) and point.recovered_purity > 0:
        oak = "FUNCTIONAL_PURIFICATION_REQUIRES_REFINING_OR_COST_REDUCTION"
        decision = "retreat_or_refine"
    elif purification_eff > 0.0 and toxicity_reduction > 0.0:
        oak = "ENVIRONMENTAL_FUNCTION_ONLY_NOT_VALORIZABLE"
        decision = "treat_as_waste_or_compliance"
    else:
        oak = "REJECTED_OR_UNPROVEN"
        decision = "reject"

    total_score = (
        0.20 * clamp01(purification_eff)
        + 0.15 * clamp01(recovery_eff)
        + 0.15 * clamp01((purity_margin + 0.2) / 0.4)
        + 0.15 * (1.0 if net_value > 0 else 0.0)
        + 0.15 * clamp01(toxicity_reduction)
        + 0.20 * proof_score
    )

    return MRVScore(
        name=point.name,
        mass_balance_error=mass_balance_error,
        purification_efficiency=purification_eff,
        recovery_efficiency=recovery_eff,
        purity_margin=purity_margin,
        recovered_value=recovered_value,
        total_cost=total_cost,
        net_value=net_value,
        toxicity_reduction=toxicity_reduction,
        proof_score=proof_score,
        oak_status=oak,
        decision=decision,
        total_score=total_score,
    )


def main() -> None:
    scenarios = [
        MRVPoint(
            name="metal-bearing industrial wastewater",
            mass_in_kg=1000.0,
            mass_out_clean_kg=980.0,
            mass_recovered_kg=5.0,
            mass_waste_kg=15.0,
            target_concentration_in=0.006,
            target_concentration_out=0.0008,
            recovered_purity=0.82,
            market_required_purity=0.75,
            recovered_unit_value_per_kg=18.0,
            energy_cost=20.0,
            maintenance_cost=15.0,
            compliance_cost=8.0,
            waste_cost=5.0,
            regeneration_cost=6.0,
            toxicity_input=0.9,
            toxicity_output=0.2,
            raman_snr_gain=2.5,
            fouling_penalty=0.25,
        ),
        MRVPoint(
            name="room air VOC compliance stream",
            mass_in_kg=100.0,
            mass_out_clean_kg=99.0,
            mass_recovered_kg=0.05,
            mass_waste_kg=0.95,
            target_concentration_in=0.001,
            target_concentration_out=0.0002,
            recovered_purity=0.30,
            market_required_purity=0.80,
            recovered_unit_value_per_kg=2.0,
            energy_cost=2.0,
            maintenance_cost=1.0,
            compliance_cost=0.5,
            waste_cost=0.2,
            regeneration_cost=0.3,
            toxicity_input=0.35,
            toxicity_output=0.08,
            raman_snr_gain=1.8,
            fouling_penalty=0.15,
        ),
        MRVPoint(
            name="overclaimed rare-metal trace stream",
            mass_in_kg=1000.0,
            mass_out_clean_kg=990.0,
            mass_recovered_kg=0.01,
            mass_waste_kg=8.0,
            target_concentration_in=0.00001,
            target_concentration_out=0.000009,
            recovered_purity=0.20,
            market_required_purity=0.95,
            recovered_unit_value_per_kg=500.0,
            energy_cost=100.0,
            maintenance_cost=50.0,
            compliance_cost=20.0,
            waste_cost=10.0,
            regeneration_cost=15.0,
            toxicity_input=0.4,
            toxicity_output=0.38,
            raman_snr_gain=0.9,
            fouling_penalty=0.7,
        ),
    ]
    for scenario in scenarios:
        print(score_mrv(scenario))


if __name__ == "__main__":
    main()
