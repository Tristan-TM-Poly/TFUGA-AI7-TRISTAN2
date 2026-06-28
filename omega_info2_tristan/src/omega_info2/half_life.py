"""Information half-life utilities for Ω-INFO²-T."""

from __future__ import annotations

from math import exp, log

from .models import clamp01

DEFAULT_HALF_LIFE_DAYS: dict[str, float] = {
    "mathematical_proof": 100_000.0,
    "physical_constant": 100_000.0,
    "scientific_review": 1_825.0,
    "experimental_calibration": 180.0,
    "software_api": 90.0,
    "patent_status": 30.0,
    "law_regulation": 180.0,
    "market_price": 1.0,
    "geopolitical_news": 0.5,
    "theory_speculation": 30.0,
    "general": 365.0,
}


def half_life_days(domain: str) -> float:
    """Return default information half-life for a domain."""
    return DEFAULT_HALF_LIFE_DAYS.get(domain, DEFAULT_HALF_LIFE_DAYS["general"])


def freshness_score(age_days: float, domain: str = "general") -> float:
    """Exponential freshness score in [0, 1].

    A score of 0.5 means the information is one half-life old.
    """
    hl = max(half_life_days(domain), 1e-9)
    decay = log(2.0) / hl
    return clamp01(exp(-decay * max(0.0, age_days)))


def age_days_from_iso(date_string: str, today_iso: str) -> float:
    """Compute approximate age in days from ISO dates, using stdlib only."""
    from datetime import date

    start = date.fromisoformat(date_string[:10])
    today = date.fromisoformat(today_iso[:10])
    return max(0, (today - start).days)
