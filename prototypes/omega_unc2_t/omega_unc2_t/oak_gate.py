"""OAK-U²Gate: status and action recommendations."""

from __future__ import annotations

from .u2_types import OAKU2Result


def oak_u2_gate(score: dict[str, float]) -> OAKU2Result:
    """Map scalar scores to an OAK-safe status.

    BLACK blocks autonomous action. RED/ORANGE require falsification/prototype.
    GREEN+ can be used locally with the stated validity domain.
    """

    u1 = float(score["u1"])
    u2 = float(score["u2"])
    risk = float(score["risk"])
    maturity = float(score["maturity"])
    debt = float(score.get("confidence_debt", 0.0))
    priority = float(score.get("priority", 0.0))
    rationale: list[str] = []

    if risk >= 0.80 or debt >= 0.80:
        status = "BLACK"
        action = "Block autonomous deployment; require human review, new evidence, and explicit OAK sign-off."
        rationale.append("Very high risk or confidence debt.")
    elif risk >= 0.55 or debt >= 0.60:
        status = "RED"
        action = "Do not canonize; run falsification tests and log M⁻ if overconfidence is confirmed."
        rationale.append("High U² risk or overconfidence debt.")
    elif u2 >= 0.65 and priority >= 0.50:
        status = "ORANGE"
        action = "Prototype privately; prioritize experiments that reduce U2 and residual volatility."
        rationale.append("High meta-uncertainty but fertile enough to test.")
    elif maturity >= 0.75 and risk <= 0.20 and debt <= 0.20:
        status = "BLUE"
        action = "Canonize provisionally with domain limits, residual monitoring, and half-life review."
        rationale.append("High maturity and low risk, but not absolute truth.")
    elif maturity >= 0.55 and risk <= 0.30:
        status = "GREEN"
        action = "Use locally with stated validity domain and continue residual logging."
        rationale.append("Locally robust enough for bounded use.")
    else:
        status = "YELLOW"
        action = "Keep as plausible hypothesis; add sources, baselines, and counter-hypotheses."
        rationale.append("Plausible but incomplete.")

    if u1 == 0.0:
        rationale.append("No U1 declared; claim may be under-specified.")
    if u2 == 0.0:
        rationale.append("No U2 declared; confidence may be non-auditable.")

    return OAKU2Result(
        status=status,  # type: ignore[arg-type]
        u1=u1,
        u2=u2,
        risk=risk,
        maturity=maturity,
        confidence_debt=debt,
        priority=priority,
        next_action=action,
        rationale=rationale,
    )
