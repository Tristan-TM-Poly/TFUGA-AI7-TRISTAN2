"""LabOAKBench engine for professor-facing lab packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .zero_touch_oak import OAKCompileResult, compile_oak


@dataclass(frozen=True)
class LabInput:
    title: str
    hypothesis: str
    measurands: Tuple[str, ...]
    instruments: Tuple[str, ...] = ()
    known_artifacts: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LabOAKBenchPacket:
    lab_title: str
    protocol_steps: Tuple[str, ...]
    uncertainty_sources: Tuple[str, ...]
    coherence_tests: Tuple[str, ...]
    artifact_controls: Tuple[str, ...]
    oak: OAKCompileResult
    next_action: str


def generate_lab_oakbench(lab: LabInput, evidence_count: int = 1) -> LabOAKBenchPacket:
    protocol_steps = (
        f"state_hypothesis: {lab.hypothesis}",
        "record_environment_and_instrument_state",
        "collect_raw_measurements",
        "estimate_uncertainty_for_each_measurand",
        "run_coherence_tests",
        "separate_measurement_model_residual_and_claim",
    )
    uncertainty_sources = tuple(
        f"uncertainty_for_{measurand}" for measurand in lab.measurands
    ) + tuple(f"instrument_drift_{instrument}" for instrument in lab.instruments)
    coherence_tests = tuple(
        f"repeatability_test_for_{measurand}" for measurand in lab.measurands
    ) + ("unit_consistency_test", "residual_sign_test")
    artifact_controls = lab.known_artifacts or (
        "calibration_bias_check",
        "saturation_check",
        "sampling_rate_check",
    )
    benefits: Dict[str, float] = {
        "teaching": 0.78,
        "research": 0.72,
        "reproducibility": 0.84,
        "automation": 0.78,
        "feasibility": 0.70,
    }
    risks: Dict[str, float] = {
        "safety": 0.30,
        "overclaim": 0.28,
        "complexity": min(0.75, 0.10 * (len(lab.measurands) + len(lab.instruments))),
        "confidentiality": 0.10,
    }
    oak = compile_oak(lab.title, benefits, risks, evidence_count=evidence_count)
    return LabOAKBenchPacket(
        lab_title=lab.title,
        protocol_steps=protocol_steps,
        uncertainty_sources=uncertainty_sources,
        coherence_tests=coherence_tests,
        artifact_controls=artifact_controls,
        oak=oak,
        next_action="generate_protocol_markdown_and_analysis_script_stub",
    )
