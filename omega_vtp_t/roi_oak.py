"""Ω-ROI-OAK: convert scientific gains into financial decision metrics.

This module is intentionally conservative. It does not promise profits. It
translates verified savings/revenue/avoided-loss hypotheses into risk-adjusted
ROI, ROAK, payback, and NPV so opportunities can be accepted, piloted, or moved
to M^-.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class ValueComponent:
    """Positive financial contribution, optionally probability-weighted."""

    name: str
    amount: float
    probability: float = 1.0
    verified: bool = False

    @property
    def expected(self) -> float:
        return float(self.amount) * float(self.probability)


@dataclass(frozen=True)
class CostComponent:
    """Cost or loss contribution."""

    name: str
    amount: float
    required: bool = True


@dataclass(frozen=True)
class RiskComponent:
    """Risk exposure with probability and impact."""

    name: str
    probability: float
    impact: float
    tail_multiplier: float = 1.0

    @property
    def expected_loss(self) -> float:
        return float(self.probability) * float(self.impact) * float(self.tail_multiplier)


@dataclass(frozen=True)
class ROIOAKReport:
    gross_expected_value: float
    verified_value: float
    total_cost: float
    expected_risk_loss: float
    risk_adjusted_value: float
    roi: float
    roak: float
    payback_years: float | None
    npv: float
    decision: str
    oak_status: str


@dataclass(frozen=True)
class FinancialCase:
    """Financial translation of an Ω technical deployment."""

    name: str
    values: Tuple[ValueComponent, ...]
    costs: Tuple[CostComponent, ...]
    risks: Tuple[RiskComponent, ...]
    annualized: bool = True
    notes: str = ""

    def evaluate(
        self,
        *,
        discount_rate: float = 0.12,
        years: int = 1,
        roak_deploy_threshold: float = 4.5,
    ) -> ROIOAKReport:
        return evaluate_financial_case(
            self,
            discount_rate=discount_rate,
            years=years,
            roak_deploy_threshold=roak_deploy_threshold,
        )


def _safe_ratio(numerator: float, denominator: float) -> float:
    if abs(denominator) <= 1e-12:
        return float("inf") if numerator > 0 else 0.0
    return float(numerator / denominator)


def npv(cashflows: Iterable[float], discount_rate: float) -> float:
    """Net present value for cashflows where t=0 is first item."""

    if discount_rate <= -1.0:
        raise ValueError("discount_rate must be > -1")
    return float(sum(float(cf) / ((1.0 + discount_rate) ** t) for t, cf in enumerate(cashflows)))


def payback_period(initial_cost: float, annual_net_value: float) -> float | None:
    """Simple payback period in years, or None if it never pays back."""

    if annual_net_value <= 0:
        return None
    return float(initial_cost / annual_net_value)


def evaluate_financial_case(
    case: FinancialCase,
    *,
    discount_rate: float = 0.12,
    years: int = 1,
    roak_deploy_threshold: float = 4.5,
) -> ROIOAKReport:
    """Evaluate expected value, risk-adjusted ROI, ROAK, payback and NPV."""

    if years < 1:
        raise ValueError("years must be >= 1")

    gross = sum(v.expected for v in case.values)
    verified = sum(v.expected for v in case.values if v.verified)
    total_cost = sum(float(c.amount) for c in case.costs)
    expected_risk = sum(r.expected_loss for r in case.risks)
    risk_adjusted = gross - total_cost - expected_risk
    roi = _safe_ratio(risk_adjusted, total_cost)
    roak = _safe_ratio(verified - total_cost - expected_risk, total_cost)
    payback = payback_period(total_cost, gross - expected_risk)

    cashflows = [-total_cost] + [gross - expected_risk for _ in range(years)]
    case_npv = npv(cashflows, discount_rate)

    if roak >= roak_deploy_threshold and risk_adjusted > 0:
        decision = "deploy"
    elif roi >= 1.0 and risk_adjusted > 0:
        decision = "pilot"
    elif risk_adjusted > 0:
        decision = "research_only"
    else:
        decision = "no_go_m_minus"

    if decision == "deploy":
        status = "oak_finance_deploy_candidate"
    elif decision == "pilot":
        status = "oak_finance_pilot_candidate"
    elif decision == "research_only":
        status = "oak_finance_research_only"
    else:
        status = "oak_finance_m_minus"

    return ROIOAKReport(
        gross_expected_value=float(gross),
        verified_value=float(verified),
        total_cost=float(total_cost),
        expected_risk_loss=float(expected_risk),
        risk_adjusted_value=float(risk_adjusted),
        roi=float(roi),
        roak=float(roak),
        payback_years=payback,
        npv=float(case_npv),
        decision=decision,
        oak_status=status,
    )


def datacenter_pue_case(
    *,
    total_power_mw: float,
    current_pue: float,
    target_pue: float,
    electricity_cost_per_kwh: float,
    deployment_cost: float,
    verification_probability: float = 0.7,
) -> FinancialCase:
    """Template for datacenter thermal optimization.

    If total_power_mw is total facility power, power saved is estimated as:
        total_power_mw * (1 - target_pue/current_pue)
    """

    if total_power_mw <= 0 or current_pue <= 0 or target_pue <= 0:
        raise ValueError("power and PUE values must be positive")
    saved_mw = max(0.0, total_power_mw * (1.0 - target_pue / current_pue))
    annual_savings = saved_mw * 1000.0 * 8760.0 * electricity_cost_per_kwh
    return FinancialCase(
        name="datacenter_pue_optimization",
        values=(ValueComponent("verified_energy_savings", annual_savings, verification_probability, verified=True),),
        costs=(CostComponent("deployment_and_integration", deployment_cost),),
        risks=(RiskComponent("thermal_operational_risk", 0.05, 0.1 * annual_savings),),
        notes="Savings should be verified by metered A/B testing against baseline load and weather.",
    )


def battery_revaluation_case(
    *,
    acquisition_cost: float,
    recondition_cost: float,
    estimated_revalued_asset: float,
    validation_probability: float,
    safety_risk_loss: float,
) -> FinancialCase:
    """Template for BESS/battery asset revaluation."""

    gross_uplift = max(0.0, estimated_revalued_asset - acquisition_cost)
    return FinancialCase(
        name="battery_asset_revaluation",
        values=(ValueComponent("asset_revaluation_uplift", gross_uplift, validation_probability, verified=False),),
        costs=(
            CostComponent("acquisition", acquisition_cost),
            CostComponent("reconditioning_and_testing", recondition_cost),
        ),
        risks=(RiskComponent("safety_or_failure_tail_loss", 0.05, safety_risk_loss, tail_multiplier=1.5),),
        notes="Requires physical validation, BMS history, safety review, and warranty/legal checks.",
    )


def hft_risk_engine_case(
    *,
    daily_volume: float,
    edge_bps: float,
    trading_days: int,
    fill_probability: float,
    infrastructure_cost: float,
    tail_loss: float,
    compliance_cost: float,
) -> FinancialCase:
    """Template for a finance risk/regime engine, not a profit guarantee.

    edge_bps is basis points of net opportunity before risk/cost adjustment.
    1 bps = 0.01% = 0.0001.
    """

    if daily_volume < 0 or trading_days < 1:
        raise ValueError("daily_volume must be nonnegative and trading_days >= 1")
    annual_opportunity = daily_volume * (edge_bps * 1e-4) * trading_days
    return FinancialCase(
        name="hft_regime_risk_engine",
        values=(ValueComponent("expected_execution_edge", annual_opportunity, fill_probability, verified=False),),
        costs=(
            CostComponent("infrastructure_and_market_data", infrastructure_cost),
            CostComponent("compliance_and_controls", compliance_cost),
        ),
        risks=(RiskComponent("tail_execution_loss", 0.02, tail_loss, tail_multiplier=2.0),),
        notes="Use first as simulator/risk engine with kill-switches; live trading requires legal/compliance review.",
    )
