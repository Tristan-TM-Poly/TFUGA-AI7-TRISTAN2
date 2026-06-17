"""Omega-OAK-Humanity attractor / repulsor / black-hole scorer.

Classifies an application by beneficial attractor score, risk repulsor score,
and black-hole danger triggers. This is a governance scaffold, not a legal or
complete safety certification tool.

Run:
    python examples/omega_oak_humanity_field_score.py
"""

from __future__ import annotations

from dataclasses import dataclass


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass(frozen=True)
class EthicalApplication:
    name: str
    life_benefit: float
    ecological_repair: float
    truth_measurement: float
    community_benefit: float
    openness_auditability: float
    abuse_potential: float
    unsafe_autonomy: float
    capture_risk: float
    surveillance_risk: float
    conflict_or_coercion_fit: float
    reversibility: float
    proof_strength: float


@dataclass(frozen=True)
class EthicalFieldScore:
    name: str
    attractor_score: float
    repulsor_score: float
    black_hole_trigger: bool
    classification: str
    release_tier: str
    negative_memory: dict[str, str]


def score_ethics(app: EthicalApplication) -> EthicalFieldScore:
    attractor = (
        0.22 * clamp01(app.life_benefit)
        + 0.18 * clamp01(app.ecological_repair)
        + 0.18 * clamp01(app.truth_measurement)
        + 0.18 * clamp01(app.community_benefit)
        + 0.12 * clamp01(app.openness_auditability)
        + 0.06 * clamp01(app.reversibility)
        + 0.06 * clamp01(app.proof_strength)
    )

    repulsor = (
        0.23 * clamp01(app.abuse_potential)
        + 0.20 * clamp01(app.unsafe_autonomy)
        + 0.18 * clamp01(app.capture_risk)
        + 0.18 * clamp01(app.surveillance_risk)
        + 0.21 * clamp01(app.conflict_or_coercion_fit)
    )

    black_hole = (
        app.abuse_potential > 0.85
        or app.conflict_or_coercion_fit > 0.85
        or (app.unsafe_autonomy > 0.75 and app.reversibility < 0.3)
        or (app.surveillance_risk > 0.75 and app.openness_auditability < 0.4)
    )

    if black_hole:
        classification = "BLACK_HOLE_QUARANTINE"
        release_tier = "Tier Black-Hole: no operational release; retain safety invariant only"
    elif attractor > repulsor and attractor > 0.65 and app.proof_strength > 0.5:
        classification = "ATTRACTOR_FOR_GOOD"
        release_tier = "Tier Prototype/Public depending on technical sensitivity"
    elif attractor > repulsor:
        classification = "BENIGN_BUT_NEEDS_PROOF"
        release_tier = "Tier Public abstraction or controlled prototype"
    else:
        classification = "REPULSOR_REDESIGN_REQUIRED"
        release_tier = "Tier Restricted until guardrails and redesign exist"

    negative_memory = {}
    if classification in {"BLACK_HOLE_QUARANTINE", "REPULSOR_REDESIGN_REQUIRED"}:
        negative_memory = {
            "hazard_pattern": "high-risk ethical field signature",
            "abuse_route": "not operationalized; stored abstractly",
            "required_guardrail": "reduce autonomy/access, add auditability, reversibility, proof, and anti-capture controls",
            "safe_reformulation": "retain only benign purification/measurement/repair branch",
        }

    return EthicalFieldScore(
        name=app.name,
        attractor_score=attractor,
        repulsor_score=repulsor,
        black_hole_trigger=black_hole,
        classification=classification,
        release_tier=release_tier,
        negative_memory=negative_memory,
    )


def main() -> None:
    applications = [
        EthicalApplication(
            name="AI7 water purification with public OAK records",
            life_benefit=0.95,
            ecological_repair=0.90,
            truth_measurement=0.85,
            community_benefit=0.80,
            openness_auditability=0.85,
            abuse_potential=0.15,
            unsafe_autonomy=0.20,
            capture_risk=0.30,
            surveillance_risk=0.10,
            conflict_or_coercion_fit=0.05,
            reversibility=0.80,
            proof_strength=0.65,
        ),
        EthicalApplication(
            name="closed industrial recovery platform with monopoly capture risk",
            life_benefit=0.60,
            ecological_repair=0.70,
            truth_measurement=0.50,
            community_benefit=0.25,
            openness_auditability=0.20,
            abuse_potential=0.45,
            unsafe_autonomy=0.35,
            capture_risk=0.85,
            surveillance_risk=0.35,
            conflict_or_coercion_fit=0.25,
            reversibility=0.45,
            proof_strength=0.45,
        ),
        EthicalApplication(
            name="unsafe autonomous coercive dual-use deployment",
            life_benefit=0.10,
            ecological_repair=0.10,
            truth_measurement=0.15,
            community_benefit=0.05,
            openness_auditability=0.05,
            abuse_potential=0.95,
            unsafe_autonomy=0.90,
            capture_risk=0.80,
            surveillance_risk=0.85,
            conflict_or_coercion_fit=0.95,
            reversibility=0.10,
            proof_strength=0.20,
        ),
    ]
    for app in applications:
        print(score_ethics(app))


if __name__ == "__main__":
    main()
