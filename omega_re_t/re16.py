"""RE-16 deterministic benchmark catalogue."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from json import dumps
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    family: str
    title: str
    objective: str
    truth_model: Mapping[str, Any]
    observations: tuple[Mapping[str, Any], ...]
    candidate_models: tuple[Mapping[str, Any], ...]
    budget: Mapping[str, Any]
    expected: Mapping[str, Any]
    negative_controls: tuple[str, ...]
    failure_modes: tuple[str, ...]
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def digest(self) -> str:
        return sha256(
            dumps(
                asdict(self),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest()


def _case(
    case_id: str,
    family: str,
    title: str,
    *,
    objective: str,
    truth: Mapping[str, Any],
    observations: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
    expected: Mapping[str, Any],
    negative: tuple[str, ...],
    failures: tuple[str, ...],
    tags: tuple[str, ...],
) -> BenchmarkCase:
    return BenchmarkCase(
        case_id,
        family,
        title,
        objective,
        truth,
        tuple(observations),
        tuple(candidates),
        {
            "max_experiments": 64,
            "max_sequence_length": 8,
            "cost": 100.0,
        },
        expected,
        negative,
        failures,
        tags,
        {
            "synthetic": True,
            "authorization": "research_sandbox",
            "schema": "omega-re-benchmark/0.2",
        },
    )


def catalog() -> tuple[BenchmarkCase, ...]:
    cases = [
        _case(
            "RE16-01",
            "automata",
            "Deterministic Mealy recovery",
            objective="recover behavioral equivalence class",
            truth={"type": "mealy", "states": 2},
            observations=[{"inputs": "A", "outputs": "0"}],
            candidates=[
                {"id": "m1", "states": 2},
                {"id": "m2", "states": 2},
            ],
            expected={
                "identifiability_level": "I2",
                "active_beats_passive": True,
            },
            negative=("permuted_state_labels",),
            failures=("internal_identity_claim",),
            tags=("fsm", "active"),
        ),
        _case(
            "RE16-02",
            "automata",
            "Hidden unreachable state",
            objective="avoid claiming inaccessible structure",
            truth={"type": "mealy", "states": 3, "reachable": 2},
            observations=[{"inputs": "AB", "outputs": "01"}],
            candidates=[
                {"id": "two", "states": 2},
                {"id": "three", "states": 3},
            ],
            expected={
                "equivalence_class_size": 2,
                "identifiability_level": "I2",
            },
            negative=("force_unreachable_state",),
            failures=("state_count_overclaim",),
            tags=("nonidentifiable",),
        ),
        _case(
            "RE16-03",
            "probabilistic",
            "Stochastic output separation",
            objective="separate output distributions",
            truth={"type": "probabilistic_mealy", "p": 0.75},
            observations=[
                {
                    "inputs": "AB",
                    "counts": {"01": 75, "00": 25},
                }
            ],
            candidates=[
                {"id": "p75", "p": 0.75},
                {"id": "p25", "p": 0.25},
            ],
            expected={
                "posterior_top": "p75",
                "calibration_required": True,
            },
            negative=("shuffle_counts",),
            failures=("noise_as_state",),
            tags=("probability",),
        ),
        _case(
            "RE16-04",
            "timed",
            "Latency-only distinction",
            objective="distinguish equal outputs using time",
            truth={"type": "timed_mealy", "latency": 0.55},
            observations=[
                {
                    "inputs": "AB",
                    "outputs": "01",
                    "latencies": [0.1, 0.54],
                }
            ],
            candidates=[
                {"id": "fast", "latency": 0.3},
                {"id": "slow", "latency": 0.55},
            ],
            expected={
                "posterior_top": "slow",
                "output_only_insufficient": True,
            },
            negative=("remove_timestamps",),
            failures=("ignore_timing",),
            tags=("timed",),
        ),
        _case(
            "RE16-05",
            "formats",
            "Fixed record grammar",
            objective="infer fixed-width fields",
            truth={"type": "record", "widths": [2, 4, 1]},
            observations=[
                {"sample": "AB1234Z"},
                {"sample": "CD5678Y"},
            ],
            candidates=[{"id": "2-4-1"}, {"id": "3-3-1"}],
            expected={"grammar": "2-4-1"},
            negative=("truncated_record",),
            failures=("single_sample_overfit",),
            tags=("format",),
        ),
        _case(
            "RE16-06",
            "formats",
            "Optional field version",
            objective="separate versions and optional fields",
            truth={"type": "tagged", "versions": [1, 2]},
            observations=[
                {"sample": "V1|A|B"},
                {"sample": "V2|A|B|C"},
            ],
            candidates=[
                {"id": "optional_c"},
                {"id": "mixed_versions"},
            ],
            expected={"keep_alternatives": True},
            negative=("unknown_version",),
            failures=("merge_versions",),
            tags=("version",),
        ),
        _case(
            "RE16-07",
            "protocols",
            "Handshake state",
            objective="infer order-dependent responses",
            truth={"type": "protocol", "states": ["new", "ready"]},
            observations=[
                {
                    "messages": ["HELLO", "DATA"],
                    "responses": ["OK", "ACK"],
                }
            ],
            candidates=[{"id": "stateful"}, {"id": "stateless"}],
            expected={"posterior_top": "stateful"},
            negative=("DATA_before_HELLO",),
            failures=("ignore_order",),
            tags=("protocol",),
        ),
        _case(
            "RE16-08",
            "protocols",
            "Retry and timeout",
            objective="infer retry transition from delayed response",
            truth={"type": "timed_protocol", "timeout": 1.0},
            observations=[
                {
                    "messages": ["REQ", "REQ"],
                    "times": [0, 1.1],
                }
            ],
            candidates=[{"id": "retry"}, {"id": "duplicate"}],
            expected={"temporal_evidence_required": True},
            negative=("retry_before_timeout",),
            failures=("duplicate_as_retry",),
            tags=("protocol", "timed"),
        ),
        _case(
            "RE16-09",
            "physical",
            "Damped oscillator",
            objective="estimate damping and frequency",
            truth={"type": "ode", "omega": 2.0, "zeta": 0.1},
            observations=[{"t": 0, "x": 1}, {"t": 1, "x": -0.34}],
            candidates=[{"id": "damped"}, {"id": "undamped"}],
            expected={
                "model": "damped",
                "parameter_uncertainty": True,
            },
            negative=("zero_damping",),
            failures=("fit_without_units",),
            tags=("physics",),
        ),
        _case(
            "RE16-10",
            "physical",
            "Thermal first-order system",
            objective="recover time constant",
            truth={"type": "first_order", "tau": 10},
            observations=[
                {"t": 0, "temperature": 20},
                {"t": 10, "temperature": 32.6},
            ],
            candidates=[{"id": "tau10"}, {"id": "tau2"}],
            expected={"posterior_top": "tau10"},
            negative=("sensor_offset",),
            failures=("offset_as_dynamics",),
            tags=("thermal",),
        ),
        _case(
            "RE16-11",
            "hybrid",
            "Thermostat hysteresis",
            objective="infer discrete modes and continuous evolution",
            truth={"type": "hybrid", "on": 18, "off": 22},
            observations=[
                {"temperature": 17.9, "mode": "on"},
                {"temperature": 22.1, "mode": "off"},
            ],
            candidates=[
                {"id": "hysteresis"},
                {"id": "single_threshold"},
            ],
            expected={"model": "hysteresis"},
            negative=("reverse_thresholds",),
            failures=("continuous_only",),
            tags=("hybrid",),
        ),
        _case(
            "RE16-12",
            "process",
            "Approval loop",
            objective="recover repeated review stage",
            truth={"type": "process", "loop": "review-rework"},
            observations=[
                {
                    "events": [
                        "draft",
                        "review",
                        "rework",
                        "review",
                        "approved",
                    ]
                }
            ],
            candidates=[{"id": "loop"}, {"id": "linear"}],
            expected={"posterior_top": "loop"},
            negative=("direct_approval",),
            failures=("declared_process_bias",),
            tags=("process",),
        ),
        _case(
            "RE16-13",
            "versions",
            "Regression lineage",
            objective="locate first behavior-changing version",
            truth={"versions": [1, 2, 3, 4], "regression": 3},
            observations=[
                {"version": 2, "pass": True},
                {"version": 3, "pass": False},
            ],
            candidates=[{"id": "change3"}, {"id": "change4"}],
            expected={"change_point": 3},
            negative=("nonmonotone_history",),
            failures=("latest_commit_blame",),
            tags=("genealogy",),
        ),
        _case(
            "RE16-14",
            "ai_behavior",
            "Context-sensitive rule",
            objective="map behavior without inferring inaccessible weights",
            truth={"type": "classifier", "context_rule": True},
            observations=[
                {"prompt": "A", "context": "X", "label": 1},
                {"prompt": "A", "context": "Y", "label": 0},
            ],
            candidates=[{"id": "contextual"}, {"id": "fixed"}],
            expected={"behavioral_map_only": True},
            negative=("paraphrase",),
            failures=("architecture_claim",),
            tags=("ai", "behavior"),
        ),
        _case(
            "RE16-15",
            "residuals",
            "Unknown model class",
            objective="detect structured residual unsupported by atlas",
            truth={"type": "piecewise_nonlinear"},
            observations=[{"residuals": [0, 0.1, 0.4, 0.9, 1.6]}],
            candidates=[{"id": "linear"}, {"id": "quadratic"}],
            expected={"unknown_unknown_flag": True},
            negative=("white_noise",),
            failures=("force_best_bad_model",),
            tags=("residual",),
        ),
        _case(
            "RE16-16",
            "cleanroom",
            "Behavioral specification",
            objective="generate neutral spec from authorized observations",
            truth={
                "type": "interface",
                "operations": ["encode", "decode"],
            },
            observations=[
                {"input": "A", "encoded": "41"},
                {"input": "B", "encoded": "42"},
            ],
            candidates=[{"id": "ascii_like"}, {"id": "lookup"}],
            expected={
                "implementation_independence": True,
                "retain_alternatives": True,
            },
            negative=("source_code_similarity",),
            failures=("copy_internal_expression",),
            tags=("cleanroom",),
        ),
    ]
    assert len({case.case_id for case in cases}) == 16
    return tuple(cases)


def catalog_digest(
    cases: Iterable[BenchmarkCase] | None = None,
) -> str:
    selected = tuple(cases or catalog())
    payload = [
        {**asdict(case), "digest": case.digest}
        for case in selected
    ]
    return sha256(
        dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def validate_catalog(
    cases: Iterable[BenchmarkCase] | None = None,
) -> tuple[str, ...]:
    selected = tuple(cases or catalog())
    issues: list[str] = []
    identifiers = [case.case_id for case in selected]
    if len(identifiers) != len(set(identifiers)):
        issues.append("duplicate_case_id")
    for case in selected:
        if not case.observations:
            issues.append(f"{case.case_id}:missing_observations")
        if not case.candidate_models:
            issues.append(f"{case.case_id}:missing_candidates")
        if not case.negative_controls:
            issues.append(f"{case.case_id}:missing_negative_controls")
        if not case.failure_modes:
            issues.append(f"{case.case_id}:missing_failure_modes")
        if not case.metadata.get("synthetic"):
            issues.append(f"{case.case_id}:not_synthetic")
    return tuple(issues)
