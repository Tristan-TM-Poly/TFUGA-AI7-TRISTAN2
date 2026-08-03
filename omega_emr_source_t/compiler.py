"""Deterministic inverse compiler from a spectrum target to source families."""

from __future__ import annotations

from .atlas import MECHANISMS
from .classifier import classify_frequency
from .models import Mechanism, MechanismCandidate, SourcePlan, SpectrumTarget
from .safety import assess_safety


def _candidate(target: SpectrumTarget, mechanism: Mechanism) -> MechanismCandidate:
    reasons: list[str] = []
    blockers: list[str] = []
    score = 0.0

    if mechanism.supports(target.center_frequency_hz):
        score += 0.52
        reasons.append("target center frequency lies inside the mechanism domain")
    else:
        blockers.append("target center frequency lies outside the mechanism domain")

    broad = any(
        token in mechanism.spectral_character
        for token in ("broad", "continuum", "band", "comb")
    )
    narrow = any(
        token in mechanism.spectral_character
        for token in ("narrow", "line", "resonant")
    )
    if target.fractional_bandwidth >= 0.1:
        if broad:
            score += 0.14
            reasons.append("spectral character supports a broad target")
        elif narrow:
            score -= 0.08
    elif target.bandwidth_hz > 0:
        if narrow:
            score += 0.08
            reasons.append("spectral character supports selective emission")
        elif broad:
            score += 0.03

    coherence = target.coherence.lower()
    if coherence in {"high", "coherent", "phase_locked"}:
        if "high" in mechanism.coherence_capabilities:
            score += 0.18
            reasons.append("mechanism can support high coherence")
        else:
            score -= 0.14
            blockers.append("requested high coherence is not represented in the atlas")
    elif coherence in {"low", "incoherent"}:
        if "incoherent" in mechanism.coherence_capabilities:
            score += 0.12
            reasons.append("mechanism naturally supports incoherent emission")
    elif coherence in mechanism.coherence_capabilities:
        score += 0.08

    if target.modulation_bandwidth_hz > 0:
        if mechanism.mechanism_id in {
            "oscillating_charge_current",
            "semiconductor_recombination",
            "stimulated_emission_laser",
            "photomixing",
        }:
            score += 0.08
            reasons.append("mechanism is compatible with direct or external modulation")
        else:
            score -= 0.03

    if target.temporal_profile.lower() in {"pulse", "pulsed", "ultrashort"}:
        if mechanism.mechanism_id in {
            "semiconductor_recombination",
            "stimulated_emission_laser",
            "nonlinear_frequency_conversion",
            "synchrotron_undulator",
        }:
            score += 0.08
            reasons.append("pulsed operation is represented by this mechanism family")

    safety = assess_safety(target, mechanism)
    reasons.extend(safety.reasons)
    if safety.status == "blocked":
        blockers.extend(safety.reasons)
    elif safety.status in {"review", "institutional_only"}:
        score -= 0.04

    score = round(max(0.0, min(1.0, score)), 4)
    if blockers:
        status = "rejected"
    elif safety.status in {"review", "institutional_only"} or score < 0.68:
        status = "conditional"
    else:
        status = "recommended"

    return MechanismCandidate(
        mechanism_id=mechanism.mechanism_id,
        label=mechanism.label,
        score=score,
        status=status,
        reasons=tuple(dict.fromkeys(reasons)),
        blockers=tuple(dict.fromkeys(blockers)),
        required_prototype_tier=safety.required_prototype_tier,
        proposed_devices=mechanism.device_families,
        simulation_models=mechanism.simulation_models,
        metrology_families=mechanism.metrology_families,
    )


def _architecture(target: SpectrumTarget, region: str) -> tuple[str, ...]:
    blocks = [
        "Driver: bounded and instrumented input energy",
        "Transducer: selected physical emission mechanism",
        "Resonator/selector: optional spectral and modal selection",
        "Guide/aperture: controlled transport or radiation boundary",
        "Modulator: temporal, frequency, phase or spatial control",
        "Stabilizer: feedback for drift, temperature and power",
        "Detector: calibrated in-band and out-of-band measurement",
        "SafetyGate: enclosure, permissions, interlocks and stop conditions",
    ]
    if region in {"radio", "microwave_and_millimeter", "terahertz_and_submillimeter"}:
        blocks.append("RF containment: shielding or matched load before radiating tests")
    if target.temporal_profile.lower() in {"pulse", "pulsed", "ultrashort"}:
        blocks.append("Timing chain: trigger, synchronization and pulse diagnostics")
    return tuple(blocks)


def compile_source(target: SpectrumTarget) -> SourcePlan:
    spectral = classify_frequency(target.center_frequency_hz)
    candidates = tuple(_candidate(target, mechanism) for mechanism in MECHANISMS)
    recommended = tuple(
        sorted(
            (candidate for candidate in candidates if candidate.status == "recommended"),
            key=lambda candidate: (-candidate.score, candidate.mechanism_id),
        )
    )
    conditional = tuple(
        sorted(
            (candidate for candidate in candidates if candidate.status == "conditional"),
            key=lambda candidate: (-candidate.score, candidate.mechanism_id),
        )
    )
    rejected = tuple(
        sorted(
            (candidate for candidate in candidates if candidate.status == "rejected"),
            key=lambda candidate: (-candidate.score, candidate.mechanism_id),
        )
    )

    selected = recommended[:3] or conditional[:3]
    metrology: list[str] = [
        "measure center frequency, occupied bandwidth and out-of-band emissions",
        "measure delivered or radiated power with traceable calibration",
        "record environmental conditions and an uncertainty budget",
        "compare measured spectrum with the target and a baseline source",
    ]
    for candidate in selected:
        metrology.extend(candidate.metrology_families)

    target_safety = assess_safety(target, classification=spectral)
    selected_safety = target_safety
    if selected:
        selected_mechanism = next(
            mechanism
            for mechanism in MECHANISMS
            if mechanism.mechanism_id == selected[0].mechanism_id
        )
        selected_safety = assess_safety(target, selected_mechanism, spectral)

    assumptions = (
        "Atlas ranges are broad engineering envelopes, not guaranteed device performance.",
        "A candidate score is a deterministic routing heuristic, not a probability of success.",
        "Energy conservation, material dispersion and thermal limits remain mandatory.",
        "Simulation does not certify fabrication, exposure, legality or scientific validity.",
    )

    return SourcePlan(
        target=target,
        spectral_region=spectral.region,
        wavelength_m=spectral.wavelength_m,
        photon_energy_ev=spectral.photon_energy_ev,
        ionizing_candidate=spectral.ionizing_candidate,
        recommended=recommended,
        conditional=conditional,
        rejected=rejected,
        architecture_blocks=_architecture(target, spectral.region),
        metrology_plan=tuple(dict.fromkeys(metrology)),
        safety_status=selected_safety.status,
        safety_reasons=selected_safety.reasons,
        required_controls=selected_safety.required_controls,
        assumptions=assumptions,
    )
