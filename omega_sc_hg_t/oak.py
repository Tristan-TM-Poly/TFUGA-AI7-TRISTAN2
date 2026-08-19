from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable

from .model import SuperconductingCandidate


@dataclass(frozen=True)
class TcEnvelope:
    q05_k: float
    median_k: float
    q95_k: float
    minimum_k: float
    maximum_k: float
    samples: int


@dataclass(frozen=True)
class OAKAssessment:
    candidate: str
    status: str
    score: float
    nominal_pairing_tc_k: float
    usable_tc_k: float
    robust_tc_q05_k: float
    findings: tuple[str, ...]


def _quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("values must not be empty")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = q * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def tc_uncertainty_envelope(
    candidate: SuperconductingCandidate,
    *,
    mu_star_values: Iterable[float] = (0.08, 0.10, 0.13),
    lambda_scales: Iterable[float] = (0.90, 1.00, 1.10),
    omega_scales: Iterable[float] = (0.90, 1.00, 1.10),
) -> TcEnvelope:
    values = [
        min(candidate.pairing_tc_k(mu, lambda_scale=ls, omega_scale=os), candidate.phase_ordering_ceiling_k)
        for mu in mu_star_values
        for ls in lambda_scales
        for os in omega_scales
    ]
    if not values:
        raise ValueError("uncertainty grid must contain at least one point")
    return TcEnvelope(
        q05_k=_quantile(values, 0.05),
        median_k=median(values),
        q95_k=_quantile(values, 0.95),
        minimum_k=min(values),
        maximum_k=max(values),
        samples=len(values),
    )


def audit_candidate(candidate: SuperconductingCandidate) -> OAKAssessment:
    findings: list[str] = []
    nominal = candidate.pairing_tc_k()
    usable = candidate.usable_tc_k()
    envelope = tc_uncertainty_envelope(candidate)

    stable = candidate.minimum_stability_margin >= 0.0
    if not stable:
        findings.append("FAIL: at least one phonon channel has a negative normalized stability margin")
    if not candidate.phonons:
        findings.append("FAIL: no phonon evidence channel is present")
    if candidate.lambda_total <= 0:
        findings.append("FAIL: total electron-phonon coupling is non-positive")
    if candidate.phase_ordering_ceiling_k < nominal:
        findings.append("CAUTION: phase-ordering ceiling limits the pairing estimate")
    if candidate.has_interlayer_covalent_bond:
        findings.append("INFO: interlayer covalent-bond motif present")

    components = (
        min(usable / 100.0, 1.0),
        min(envelope.q05_k / 100.0, 1.0),
        candidate.synthesis_score,
        candidate.defect_robustness,
        candidate.substrate_robustness,
        1.0 if stable else 0.0,
    )
    score = sum(components) / len(components)
    if not stable or candidate.lambda_total <= 0:
        status = "REJECT"
    elif score >= 0.70 and envelope.q05_k > 0:
        status = "PROMOTE"
    else:
        status = "RESEARCH"

    return OAKAssessment(
        candidate=candidate.name,
        status=status,
        score=score,
        nominal_pairing_tc_k=nominal,
        usable_tc_k=usable,
        robust_tc_q05_k=envelope.q05_k,
        findings=tuple(findings),
    )
