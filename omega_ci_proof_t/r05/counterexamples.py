from __future__ import annotations

from typing import Any, Mapping, Sequence

from .behaviors import resolve_behavior
from .models import Counterexample, CounterexampleReport, MutationSpec, stable_digest


def _candidate_strings(raw: Mapping[str, Any]) -> tuple[str, ...]:
    explicit = [str(value) for value in raw.get("explicit", [])]
    prefixes = [str(value) for value in raw.get("prefixes", ["", "./", "././", ".", "../"])]
    atoms = [str(value) for value in raw.get("atoms", ["a", ".github", "workflows/ci.yml"])]
    suffixes = [str(value) for value in raw.get("suffixes", ["", "/b", ".py"])]
    generated = [f"{prefix}{atom}{suffix}" for prefix in prefixes for atom in atoms for suffix in suffixes]
    return tuple(sorted(set(explicit + generated), key=lambda value: (len(value), value)))


def _minimize_string(value: str, reference, mutant) -> tuple[str, tuple[str, ...]]:
    current = value
    trace: list[str] = []
    changed = True
    while changed and len(current) > 1:
        changed = False
        candidates: list[str] = []
        if "/" in current:
            parts = current.split("/")
            for index in range(len(parts)):
                candidate = "/".join(parts[:index] + parts[index + 1 :])
                if candidate:
                    candidates.append(candidate)
        for index in range(len(current)):
            candidate = current[:index] + current[index + 1 :]
            if candidate:
                candidates.append(candidate)
        for candidate in sorted(set(candidates), key=lambda item: (len(item), item)):
            if reference(candidate) != mutant(candidate):
                trace.append(f"{current!r}->{candidate!r}")
                current = candidate
                changed = True
                break
    return current, tuple(trace)


class CounterexampleForge:
    def search(
        self,
        specs: Sequence[MutationSpec],
        surviving_mutant_ids: Sequence[str],
        seed_space: Mapping[str, Any],
        *,
        baseline_behavior: str,
        claim_id: str,
        property_id: str,
        max_candidates: int = 500,
    ) -> CounterexampleReport:
        if max_candidates <= 0:
            raise ValueError("max_candidates must be positive")
        by_id = {item.mutant_id: item for item in specs}
        reference = resolve_behavior(baseline_behavior)
        candidates = _candidate_strings(seed_space)
        evaluated = 0
        found: list[Counterexample] = []
        for mutant_id in sorted(set(surviving_mutant_ids)):
            spec = by_id.get(mutant_id)
            if spec is None:
                raise KeyError(f"unknown surviving mutant: {mutant_id}")
            mutant = resolve_behavior(spec.behavior)
            witness = None
            for candidate in candidates:
                if evaluated >= max_candidates:
                    break
                evaluated += 1
                expected = reference(candidate)
                observed = mutant(candidate)
                if expected != observed:
                    witness = (candidate, expected, observed)
                    break
            if witness is None:
                continue
            original, expected, observed = witness
            minimized, trace = _minimize_string(original, reference, mutant)
            found.append(Counterexample(
                claim_id=claim_id,
                mutant_id=mutant_id,
                property_id=property_id,
                original_input=original,
                minimized_input=minimized,
                expected_output=reference(minimized),
                observed_output=mutant(minimized),
                reduction_steps=trace,
                provenance=(
                    f"seed-space:{stable_digest(seed_space)[:16]}",
                    f"mutant:{mutant_id}",
                    f"baseline:{baseline_behavior}",
                ),
            ))
        exhausted = evaluated >= min(max_candidates, max(1, len(candidates) * max(1, len(set(surviving_mutant_ids)))))
        return CounterexampleReport(
            searched_mutant_ids=tuple(sorted(set(surviving_mutant_ids))),
            counterexamples=tuple(found),
            candidates_evaluated=evaluated,
            exhausted=exhausted,
        )
