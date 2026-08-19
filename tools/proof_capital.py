"""Proof Capital calculator for Tristan CanonOS.

ProofCapital is a conservative score: evidence and survival credits minus
risk debt and overclaim costs. It does not prove truth.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProofCapitalReport:
    capital: int
    credits: dict[str, int]
    debts: dict[str, int]
    interpretation: str
    can_upgrade_claim: bool


def calculate_proof_capital(
    *,
    tests: int = 0,
    measurements: int = 0,
    reproductions: int = 0,
    strong_sources: int = 0,
    counterworlds_survived: int = 0,
    overclaims: int = 0,
    risk_debt_points: int = 0,
) -> ProofCapitalReport:
    credits = {
        "tests": tests * 2,
        "measurements": measurements * 3,
        "reproductions": reproductions * 5,
        "strong_sources": strong_sources * 2,
        "counterworlds_survived": counterworlds_survived,
    }
    debts = {
        "overclaims": overclaims * 4,
        "risk_debt_points": risk_debt_points,
    }
    capital = sum(credits.values()) - sum(debts.values())

    if capital >= 20:
        interpretation = "strong proof capital within stated scope"
    elif capital >= 10:
        interpretation = "moderate proof capital; still needs scope limits"
    elif capital >= 1:
        interpretation = "weak positive proof capital; avoid strong claims"
    else:
        interpretation = "negative or zero proof capital; downgrade claim"

    return ProofCapitalReport(
        capital=capital,
        credits=credits,
        debts=debts,
        interpretation=interpretation,
        can_upgrade_claim=capital >= 10 and overclaims == 0,
    )
