from __future__ import annotations

from typing import Any, Mapping, Sequence

from .behaviors import resolve_behavior
from .models import MutationCampaignReport, MutationSpec, MutationTest, MutantResult, sorted_unique


def mutation_specs_from_mapping(raw: Mapping[str, Any]) -> tuple[MutationSpec, ...]:
    return tuple(
        MutationSpec(
            mutant_id=str(item["mutant_id"]),
            operator_id=str(item["operator_id"]),
            target=str(item["target"]),
            behavior=str(item["behavior"]),
            description=str(item["description"]),
            weight=float(item.get("weight", 1.0)),
            expected_equivalent=bool(item.get("expected_equivalent", False)),
            metadata=dict(item.get("metadata", {})),
        )
        for item in raw.get("mutants", [])
    )


def mutation_tests_from_mapping(raw: Mapping[str, Any]) -> tuple[MutationTest, ...]:
    return tuple(
        MutationTest(
            test_id=str(item["test_id"]),
            claim_ids=tuple(str(value) for value in item.get("claim_ids", [])),
            input_value=str(item["input"]),
            expected_output=str(item["expected"]),
            evidence_kind=str(item.get("evidence_kind", "unit")),
        )
        for item in raw.get("tests", [])
    )


class MutationCampaignEngine:
    def run(
        self,
        specs: Sequence[MutationSpec],
        tests: Sequence[MutationTest],
        *,
        target: str,
        baseline_behavior: str,
    ) -> MutationCampaignReport:
        baseline = resolve_behavior(baseline_behavior)
        if not specs:
            raise ValueError("at least one mutation spec is required")
        if not tests:
            raise ValueError("at least one mutation test is required")
        duplicate_ids = [item.mutant_id for item in specs]
        if len(duplicate_ids) != len(set(duplicate_ids)):
            raise ValueError("duplicate mutant IDs")

        for test in tests:
            observed = baseline(test.input_value)
            if observed != test.expected_output:
                raise ValueError(f"baseline fails declared test {test.test_id}: {observed!r} != {test.expected_output!r}")

        results: list[MutantResult] = []
        killed_weight = 0.0
        killable_weight = 0.0
        for spec in sorted(specs, key=lambda item: item.mutant_id):
            if spec.target != target:
                results.append(MutantResult(
                    mutant_id=spec.mutant_id,
                    operator_id=spec.operator_id,
                    status="INVALID",
                    weight=spec.weight,
                    killed_by=(),
                    surviving_tests=(),
                    observed_outputs={},
                    reason=f"target mismatch: {spec.target}",
                ))
                continue
            try:
                mutant = resolve_behavior(spec.behavior)
            except KeyError:
                results.append(MutantResult(
                    mutant_id=spec.mutant_id,
                    operator_id=spec.operator_id,
                    status="INVALID",
                    weight=spec.weight,
                    killed_by=(),
                    surviving_tests=(),
                    observed_outputs={},
                    reason=f"unknown behavior: {spec.behavior}",
                ))
                continue

            outputs = {test.test_id: mutant(test.input_value) for test in tests}
            killed_by = tuple(sorted(test.test_id for test in tests if outputs[test.test_id] != test.expected_output))
            surviving_tests = tuple(sorted(test.test_id for test in tests if outputs[test.test_id] == test.expected_output))
            equivalent_on_corpus = all(outputs[test.test_id] == baseline(test.input_value) for test in tests)

            if spec.expected_equivalent:
                status = "EQUIVALENT" if equivalent_on_corpus else "KILLED"
                reason = "declared equivalent and observationally equivalent on the campaign corpus" if status == "EQUIVALENT" else "declared equivalent but diverged on the campaign corpus"
            elif killed_by:
                status = "KILLED"
                reason = "one or more tests detected the mutant"
            else:
                status = "SURVIVED"
                reason = "the current finite test corpus did not distinguish the mutant"

            if status in {"KILLED", "SURVIVED"}:
                killable_weight += spec.weight
            if status == "KILLED":
                killed_weight += spec.weight
            results.append(MutantResult(
                mutant_id=spec.mutant_id,
                operator_id=spec.operator_id,
                status=status,
                weight=spec.weight,
                killed_by=killed_by,
                surviving_tests=surviving_tests,
                observed_outputs=outputs,
                reason=reason,
            ))

        killed = sum(item.status == "KILLED" for item in results)
        survived = sum(item.status == "SURVIVED" for item in results)
        equivalent = sum(item.status == "EQUIVALENT" for item in results)
        invalid = sum(item.status == "INVALID" for item in results)
        denominator = killed + survived
        mutation_score = round(killed / denominator, 6) if denominator else 1.0
        weighted = round(killed_weight / killable_weight, 6) if killable_weight else 1.0
        return MutationCampaignReport(
            target=target,
            baseline_behavior=baseline_behavior,
            results=tuple(results),
            generated=len(specs),
            evaluated=len(specs) - invalid,
            killed=killed,
            survived=survived,
            equivalent=equivalent,
            invalid=invalid,
            mutation_score=mutation_score,
            weighted_mutation_score=weighted,
            surviving_mutant_ids=sorted_unique(tuple(item.mutant_id for item in results if item.status == "SURVIVED")),
        )
