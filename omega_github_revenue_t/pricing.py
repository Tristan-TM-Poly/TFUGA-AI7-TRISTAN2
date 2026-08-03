from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any


@dataclass(frozen=True)
class DeliveryEstimate:
    delivery_minutes: int
    review_minutes: int
    support_minutes: int
    compute_minor: int = 0
    tooling_minor: int = 0
    contingency_fraction: float = 0.20

    def validate(self) -> None:
        if min(
            self.delivery_minutes,
            self.review_minutes,
            self.support_minutes,
            self.compute_minor,
            self.tooling_minor,
        ) < 0:
            raise ValueError("delivery estimates must be non-negative")
        if not 0 <= self.contingency_fraction <= 1:
            raise ValueError("contingency_fraction must be between 0 and 1")

    @property
    def total_minutes(self) -> int:
        return self.delivery_minutes + self.review_minutes + self.support_minutes


@dataclass(frozen=True)
class PriceEnvelope:
    floor_minor: int
    target_minor: int
    ceiling_minor: int
    currency: str
    assumptions: tuple[str, ...]


def price_envelope(
    estimate: DeliveryEstimate,
    *,
    hourly_cost_minor: int,
    currency: str = "CAD",
    target_margin_fraction: float = 0.40,
    ceiling_multiplier: float = 1.75,
) -> PriceEnvelope:
    estimate.validate()
    if hourly_cost_minor <= 0:
        raise ValueError("hourly_cost_minor must be positive")
    if len(currency) != 3:
        raise ValueError("currency must be a three-letter code")
    if not 0 <= target_margin_fraction < 1:
        raise ValueError("target_margin_fraction must be in [0, 1)")
    if ceiling_multiplier < 1:
        raise ValueError("ceiling_multiplier must be at least one")
    labour = ceil(estimate.total_minutes * hourly_cost_minor / 60)
    direct = labour + estimate.compute_minor + estimate.tooling_minor
    floor = ceil(direct * (1 + estimate.contingency_fraction))
    target = ceil(floor / max(1e-9, 1 - target_margin_fraction))
    ceiling = ceil(target * ceiling_multiplier)
    return PriceEnvelope(
        floor_minor=floor,
        target_minor=target,
        ceiling_minor=ceiling,
        currency=currency.upper(),
        assumptions=(
            f"hourly cost basis={hourly_cost_minor} minor units",
            f"estimated minutes={estimate.total_minutes}",
            f"contingency={estimate.contingency_fraction:.2f}",
            f"target contribution margin={target_margin_fraction:.2f}",
            "market willingness to pay remains unproven until observed",
        ),
    )


def delivery_economics(
    *,
    price_minor: int,
    fee_minor: int,
    estimate: DeliveryEstimate,
    hourly_cost_minor: int,
) -> dict[str, Any]:
    if price_minor < 0 or fee_minor < 0 or fee_minor > price_minor:
        raise ValueError("invalid price or fee")
    envelope = price_envelope(estimate, hourly_cost_minor=hourly_cost_minor)
    labour = ceil(estimate.total_minutes * hourly_cost_minor / 60)
    direct_cost = labour + estimate.compute_minor + estimate.tooling_minor + fee_minor
    contribution = price_minor - direct_cost
    return {
        "estimate": asdict(estimate),
        "price_minor": price_minor,
        "fee_minor": fee_minor,
        "direct_cost_minor": direct_cost,
        "contribution_minor": contribution,
        "contribution_margin": (
            None if price_minor == 0 else round(contribution / price_minor, 8)
        ),
        "price_envelope": asdict(envelope),
        "non_claim": (
            "contribution margin is not net profit, tax income, or guaranteed future margin"
        ),
    }
