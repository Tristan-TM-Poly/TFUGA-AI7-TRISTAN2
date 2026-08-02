"""Streaming catalog API for the Ω-MAIL-T R0.2 massive atlas."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterator


DEFAULT_ROOT = Path("generated/omega_mail_t_r02")


@dataclass(frozen=True, slots=True)
class ScenarioRecord:
    id: str
    sender_company: str
    recipient_company: str
    sender_role: str
    recipient_role: str
    intent: str
    classification: str
    locale: str
    urgency: str
    anomaly: str
    expected_route: str
    synthetic: bool
    external_delivery_allowed: bool

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "ScenarioRecord":
        return cls(
            id=str(raw["id"]),
            sender_company=str(raw["sender_company"]),
            recipient_company=str(raw["recipient_company"]),
            sender_role=str(raw["sender_role"]),
            recipient_role=str(raw["recipient_role"]),
            intent=str(raw["intent"]),
            classification=str(raw["classification"]),
            locale=str(raw["locale"]),
            urgency=str(raw["urgency"]),
            anomaly=str(raw["anomaly"]),
            expected_route=str(raw["expected_route"]),
            synthetic=bool(raw["synthetic"]),
            external_delivery_allowed=bool(raw["external_delivery_allowed"]),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    id: str
    scenario_id: str
    benchmark_type: str
    pass_condition: str
    negative_control: str
    status: str

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "BenchmarkRecord":
        return cls(
            id=str(raw["id"]),
            scenario_id=str(raw["scenario_id"]),
            benchmark_type=str(raw["benchmark_type"]),
            pass_condition=str(raw["pass_condition"]),
            negative_control=str(raw["negative_control"]),
            status=str(raw["status"]),
        )


def _jsonl_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.jsonl"))


def iter_raw(directory: Path) -> Iterator[dict[str, object]]:
    for path in _jsonl_files(directory):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc


def iter_scenarios(root: Path = DEFAULT_ROOT) -> Iterator[ScenarioRecord]:
    for raw in iter_raw(root / "scenarios"):
        yield ScenarioRecord.from_dict(raw)


def iter_benchmarks(root: Path = DEFAULT_ROOT) -> Iterator[BenchmarkRecord]:
    for raw in iter_raw(root / "benchmarks"):
        yield BenchmarkRecord.from_dict(raw)


def query_scenarios(
    *,
    root: Path = DEFAULT_ROOT,
    company: str | None = None,
    intent: str | None = None,
    anomaly: str | None = None,
    locale: str | None = None,
    classification: str | None = None,
    limit: int | None = None,
) -> Iterator[ScenarioRecord]:
    emitted = 0
    for record in iter_scenarios(root):
        if company and company not in {record.sender_company, record.recipient_company}:
            continue
        if intent and record.intent != intent:
            continue
        if anomaly and record.anomaly != anomaly:
            continue
        if locale and record.locale != locale:
            continue
        if classification and record.classification != classification:
            continue
        yield record
        emitted += 1
        if limit is not None and emitted >= limit:
            return


def benchmarks_for(
    scenario_id: str,
    *,
    root: Path = DEFAULT_ROOT,
) -> Iterator[BenchmarkRecord]:
    for record in iter_benchmarks(root):
        if record.scenario_id == scenario_id:
            yield record


def load_manifest(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    return json.loads((root / "manifest.json").read_text(encoding="utf-8"))


def audit(root: Path = DEFAULT_ROOT) -> dict[str, object]:
    manifest = load_manifest(root)
    scenario_ids: set[str] = set()
    benchmark_ids: set[str] = set()
    coverage: Counter[str] = Counter()
    unsafe_scenarios: list[str] = []

    for scenario in iter_scenarios(root):
        if scenario.id in scenario_ids:
            raise ValueError(f"Duplicate scenario ID: {scenario.id}")
        scenario_ids.add(scenario.id)
        if not scenario.synthetic or scenario.external_delivery_allowed:
            unsafe_scenarios.append(scenario.id)

    for benchmark in iter_benchmarks(root):
        if benchmark.id in benchmark_ids:
            raise ValueError(f"Duplicate benchmark ID: {benchmark.id}")
        benchmark_ids.add(benchmark.id)
        coverage[benchmark.scenario_id] += 1

    missing_scenarios = sorted(set(coverage) - scenario_ids)
    undercovered = sorted(
        scenario_id for scenario_id in scenario_ids if coverage[scenario_id] != 2
    )
    valid = (
        len(scenario_ids) == int(manifest["scenario_records"])
        and len(benchmark_ids) == int(manifest["benchmark_records"])
        and not missing_scenarios
        and not undercovered
        and not unsafe_scenarios
    )
    return {
        "valid": valid,
        "scenario_count": len(scenario_ids),
        "benchmark_count": len(benchmark_ids),
        "coverage_per_scenario": 2,
        "missing_scenarios": missing_scenarios,
        "undercovered": undercovered,
        "unsafe_scenarios": unsafe_scenarios,
    }
