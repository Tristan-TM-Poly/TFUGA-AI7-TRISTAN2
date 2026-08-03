"""Deterministic adversarial testing for finite or symbolic claim fixtures."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import itertools
import json
from typing import Any, Callable, Iterable, Mapping, Sequence

from .models import CounterexampleRecord


Predicate = Callable[[Mapping[str, Any]], bool]


def _digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cartesian_cases(domains: Mapping[str, Sequence[Any]]) -> tuple[dict[str, Any], ...]:
    names = tuple(sorted(domains))
    values = [tuple(domains[name]) for name in names]
    return tuple(dict(zip(names, product)) for product in itertools.product(*values))


def boundary_cases(domains: Mapping[str, Sequence[Any]]) -> tuple[dict[str, Any], ...]:
    """Generate low/high/central finite cases without inventing continuity claims."""
    normalized = {name: tuple(values) for name, values in domains.items()}
    if any(not values for values in normalized.values()):
        raise ValueError("every domain must be non-empty")
    names = tuple(sorted(normalized))
    center = {name: normalized[name][len(normalized[name]) // 2] for name in names}
    cases = [center]
    for name in names:
        for value in (normalized[name][0], normalized[name][-1]):
            candidate = dict(center)
            candidate[name] = value
            cases.append(candidate)
    unique: dict[str, dict[str, Any]] = {}
    for case in cases:
        unique[_digest(case)] = case
    return tuple(unique[key] for key in sorted(unique))


def search_counterexamples(
    *,
    claim_id: str,
    predicate: Predicate,
    cases: Iterable[Mapping[str, Any]],
    explanation: str = "predicate returned false",
    stop_after: int | None = None,
) -> tuple[CounterexampleRecord, ...]:
    if stop_after is not None and stop_after <= 0:
        raise ValueError("stop_after must be positive")
    records: list[CounterexampleRecord] = []
    for index, case in enumerate(cases):
        witness = dict(case)
        try:
            holds = bool(predicate(witness))
        except Exception as exc:  # adversarial harness records exceptions as failures
            holds = False
            local_explanation = f"predicate raised {type(exc).__name__}: {exc}"
        else:
            local_explanation = explanation
        if holds:
            continue
        digest = _digest({"claim_id": claim_id, "witness": witness, "explanation": local_explanation})
        records.append(
            CounterexampleRecord(
                counterexample_id=f"cx-{claim_id}-{index:06d}-{digest[:12]}",
                claim_id=claim_id,
                witness=witness,
                explanation=local_explanation,
                reproducible=True,
                digest=digest,
            )
        )
        if stop_after is not None and len(records) >= stop_after:
            break
    return tuple(records)


def adversarial_report(records: Iterable[CounterexampleRecord]) -> dict[str, Any]:
    items = tuple(records)
    payload = {
        "counterexamples": [asdict(item) for item in items],
        "count": len(items),
        "claim_survived_finite_harness": len(items) == 0,
        "finite_harness_is_not_proof": True,
    }
    payload["digest"] = _digest(payload)
    return payload
