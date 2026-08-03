from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class BetaPosterior:
    alpha: float
    beta: float

    def validate(self) -> None:
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("beta posterior parameters must be positive")

    @property
    def mean(self) -> float:
        self.validate()
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        self.validate()
        total = self.alpha + self.beta
        return self.alpha * self.beta / (total * total * (total + 1))

    def interval_normal_approx(self, z: float = 1.96) -> tuple[float, float]:
        if z <= 0:
            raise ValueError("z must be positive")
        radius = z * sqrt(self.variance)
        return max(0.0, self.mean - radius), min(1.0, self.mean + radius)

    def to_dict(self) -> dict[str, Any]:
        low, high = self.interval_normal_approx()
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "mean": round(self.mean, 8),
            "approx_95_interval": [round(low, 8), round(high, 8)],
        }


@dataclass(frozen=True)
class FunnelSnapshot:
    unique_visitors: int
    sponsor_page_views: int
    sponsor_clicks: int
    sponsorships: int
    service_inquiries: int
    qualified_inquiries: int
    paid_services: int
    repeat_paid_services: int

    def validate(self) -> None:
        values = asdict(self)
        if any(value < 0 for value in values.values()):
            raise ValueError("funnel counts must be non-negative")
        if self.sponsor_page_views > self.unique_visitors:
            raise ValueError("sponsor_page_views cannot exceed unique_visitors")
        if self.sponsor_clicks > self.sponsor_page_views:
            raise ValueError("sponsor_clicks cannot exceed sponsor_page_views")
        if self.sponsorships > self.sponsor_clicks:
            raise ValueError("sponsorships cannot exceed sponsor_clicks")
        if self.qualified_inquiries > self.service_inquiries:
            raise ValueError("qualified_inquiries cannot exceed service_inquiries")
        if self.paid_services > self.qualified_inquiries:
            raise ValueError("paid_services cannot exceed qualified_inquiries")
        if self.repeat_paid_services > self.paid_services:
            raise ValueError("repeat_paid_services cannot exceed paid_services")


def posterior(
    successes: int,
    trials: int,
    *,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
) -> BetaPosterior:
    if successes < 0 or trials < 0 or successes > trials:
        raise ValueError("require 0 <= successes <= trials")
    if prior_alpha <= 0 or prior_beta <= 0:
        raise ValueError("prior parameters must be positive")
    return BetaPosterior(prior_alpha + successes, prior_beta + trials - successes)


def analyze_funnel(snapshot: FunnelSnapshot) -> dict[str, Any]:
    snapshot.validate()
    stages = {
        "visitor_to_sponsor_page": (
            snapshot.sponsor_page_views,
            snapshot.unique_visitors,
        ),
        "sponsor_page_to_click": (
            snapshot.sponsor_clicks,
            snapshot.sponsor_page_views,
        ),
        "click_to_sponsorship": (
            snapshot.sponsorships,
            snapshot.sponsor_clicks,
        ),
        "inquiry_to_qualified": (
            snapshot.qualified_inquiries,
            snapshot.service_inquiries,
        ),
        "qualified_to_paid": (
            snapshot.paid_services,
            snapshot.qualified_inquiries,
        ),
        "paid_to_repeat": (
            snapshot.repeat_paid_services,
            snapshot.paid_services,
        ),
    }
    analysis: dict[str, Any] = {}
    for name, (successes, trials) in stages.items():
        analysis[name] = {
            "successes": successes,
            "trials": trials,
            "observed_rate": None if trials == 0 else round(successes / trials, 8),
            "posterior": posterior(successes, trials).to_dict(),
        }
    return {
        "snapshot": asdict(snapshot),
        "stages": analysis,
        "warnings": [
            "zero or small samples imply broad uncertainty",
            "repository traffic is not customer intent",
            "sponsorship is support, not necessarily product demand",
        ],
    }


def recommend_funnel_action(snapshot: FunnelSnapshot) -> str:
    snapshot.validate()
    if snapshot.unique_visitors < 30:
        return "collect more relevant traffic before interpreting conversion"
    if snapshot.sponsor_page_views / max(snapshot.unique_visitors, 1) < 0.05:
        return "clarify the support call-to-action and demonstrated public value"
    if snapshot.sponsor_clicks == 0:
        return "test sponsor-page clarity without changing technical claims"
    if snapshot.service_inquiries == 0:
        return "publish one bounded service demonstration and explicit scope"
    if snapshot.qualified_inquiries == 0:
        return "tighten audience and qualification criteria"
    if snapshot.paid_services == 0:
        return "test pricing, risk reversal, and delivery scope with consented prospects"
    if snapshot.repeat_paid_services == 0:
        return "measure delivered utility and reasons for non-repeat before scaling"
    return "preserve delivery quality, measure margin and retention, then scale cautiously"
