from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import csv
import io
import math
from typing import Iterable

from .microarch import file_sha256, microarchitecture_manifest


DEFAULT_PERF_EVENTS = (
    "cycles",
    "instructions",
    "branches",
    "branch-misses",
    "cache-references",
    "cache-misses",
    "task-clock",
    "context-switches",
    "page-faults",
)

HARDWARE_PERF_EVENTS = frozenset(
    {"cycles", "instructions", "branches", "branch-misses", "cache-references", "cache-misses"}
)


@dataclass(frozen=True)
class PerfCounter:
    event: str
    value: float
    unit: str | None = None
    running_percentage: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PerfParseResult:
    counters: tuple[PerfCounter, ...]
    skipped_events: dict[str, str]
    diagnostics: tuple[str, ...]


def requested_perf_events() -> tuple[str, ...]:
    return DEFAULT_PERF_EVENTS


def _parse_number(value: str) -> float | None:
    text = value.strip()
    if not text or text.startswith("<"):
        return None
    text = text.replace(" ", "")
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def _base_event(event: str) -> str:
    return event.split(":", 1)[0].strip()


def parse_perf_stat_csv(text: str, *, delimiter: str = ";") -> PerfParseResult:
    """Parse ``perf stat -x ';' --no-big-num`` output.

    The parser never executes perf. It consumes evidence emitted by a separately
    controlled collection step. Unsupported/not-counted events are recorded as
    skipped instead of being converted to zero.
    """

    counters: list[PerfCounter] = []
    skipped: dict[str, str] = {}
    diagnostics: list[str] = []
    seen: set[str] = set()

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    for row in reader:
        if not row:
            continue
        stripped = [cell.strip() for cell in row]
        if not any(stripped):
            continue
        first = stripped[0]
        if first.startswith("#"):
            continue
        if len(stripped) < 3:
            diagnostics.append(";".join(stripped)[:500])
            continue

        event = stripped[2]
        if not event:
            diagnostics.append(";".join(stripped)[:500])
            continue

        raw_value = first
        value = _parse_number(raw_value)
        if value is None:
            reason = raw_value or "missing value"
            if reason.startswith("<"):
                reason = reason.strip("<>")
            skipped[event] = reason
            continue
        if value < 0.0:
            diagnostics.append(f"negative counter rejected for {event}: {raw_value}")
            continue

        unit = stripped[1] or None
        running_percentage = None
        if len(stripped) > 4:
            candidate = _parse_number(stripped[4])
            if candidate is not None and 0.0 <= candidate <= 100.0:
                running_percentage = candidate

        if event in seen:
            diagnostics.append(f"duplicate event {event!r}; keeping first observation")
            continue
        seen.add(event)
        counters.append(
            PerfCounter(
                event=event,
                value=value,
                unit=unit,
                running_percentage=running_percentage,
            )
        )

    # Permission/tooling errors are often plain stderr lines rather than CSV.
    if not counters and not skipped:
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#"):
                diagnostics.append(cleaned[:500])
                if len(diagnostics) >= 8:
                    break

    return PerfParseResult(tuple(counters), skipped, tuple(dict.fromkeys(diagnostics)))


def _lookup(counters: Iterable[PerfCounter], event: str) -> float | None:
    for counter in counters:
        if _base_event(counter.event) == event:
            return counter.value
    return None


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0.0:
        return None
    value = numerator / denominator
    return value if math.isfinite(value) else None


def derive_counter_metrics(counters: Iterable[PerfCounter]) -> dict[str, float | None]:
    rows = tuple(counters)
    cycles = _lookup(rows, "cycles")
    instructions = _lookup(rows, "instructions")
    branches = _lookup(rows, "branches")
    branch_misses = _lookup(rows, "branch-misses")
    cache_references = _lookup(rows, "cache-references")
    cache_misses = _lookup(rows, "cache-misses")
    return {
        "ipc": _safe_ratio(instructions, cycles),
        "cycles_per_instruction": _safe_ratio(cycles, instructions),
        "branch_miss_rate": _safe_ratio(branch_misses, branches),
        "cache_miss_rate": _safe_ratio(cache_misses, cache_references),
    }


def _binary_manifest(binary_path: str | Path | None) -> dict[str, object] | None:
    if binary_path is None:
        return None
    path = Path(binary_path)
    try:
        size = path.stat().st_size
        digest = file_sha256(path)
    except OSError:
        return {"path": str(path), "exists": False, "size_bytes": None, "sha256": None}
    return {"path": str(path), "exists": True, "size_bytes": size, "sha256": digest}


def build_p5_report(
    perf_text: str,
    *,
    source_exit_code: int | None = None,
    binary_path: str | Path | None = None,
    machine: dict[str, object] | None = None,
) -> dict[str, object]:
    parsed = parse_perf_stat_csv(perf_text)
    counters = parsed.counters
    hardware_count = sum(1 for counter in counters if _base_event(counter.event) in HARDWARE_PERF_EVENTS)

    if not counters:
        availability = "unavailable"
    elif hardware_count == 0:
        availability = "partial"
    else:
        availability = "available"

    reason: str | None = None
    if availability == "unavailable":
        if parsed.diagnostics:
            # Plain perf/tooling errors are frequently multi-line (for example
            # ``Error:`` followed by the actionable permission diagnostic).
            # Preserve the bounded diagnostic context instead of truncating the
            # report reason to an uninformative first line.
            reason = " | ".join(parsed.diagnostics)
        elif parsed.skipped_events:
            reason = "all requested events were unsupported or not counted"
        elif source_exit_code not in (None, 0):
            reason = f"counter collection exited with status {source_exit_code}"
        else:
            reason = "no counter evidence was parsed"

    counter_map = {counter.event: counter.to_dict() for counter in counters}
    return {
        "schema_version": 1,
        "evidence_level": "P5-hardware-counters",
        "availability": availability,
        "claim_scope": "single_execution_context_only",
        "authority": "review_only",
        "warning": (
            "hardware-counter observations are target/context specific and do not establish universal speedups"
        ),
        "reason": reason,
        "source_exit_code": source_exit_code,
        "machine": machine if machine is not None else microarchitecture_manifest(include_toolchains=True),
        "binary": _binary_manifest(binary_path),
        "requested_events": list(DEFAULT_PERF_EVENTS),
        "hardware_event_count": hardware_count,
        "counters": counter_map,
        "skipped_events": dict(parsed.skipped_events),
        "diagnostics": list(parsed.diagnostics),
        "derived": derive_counter_metrics(counters),
        "collection_contract": {
            "collector": "perf-stat-external-controlled-step",
            "parser": "omega-asm-perf-stat-csv-v1",
            "delimiter": ";",
            "big_number_formatting": "disabled_expected",
            "arbitrary_command_execution_by_package": False,
            "unsupported_event_semantics": "unavailable_not_zero",
        },
    }
