from __future__ import annotations

from typing import Sequence

from .models import Counterexample, MMinusCompilation, MMinusRule, stable_digest


class MMinusCompiler:
    def compile(self, counterexamples: Sequence[Counterexample]) -> MMinusCompilation:
        rules: list[MMinusRule] = []
        tests: list[str] = []
        for counterexample in sorted(counterexamples, key=lambda item: item.counterexample_id):
            rule_id = f"MMINUS-R05-{stable_digest(counterexample.identity_payload())[:12].upper()}"
            test_name = f"test_mminus_{rule_id.lower().replace('-', '_')}"
            test_source = (
                f"def {test_name}():\n"
                f"    # Generated candidate from {counterexample.counterexample_id}; human review required.\n"
                f"    value = {counterexample.minimized_input!r}\n"
                f"    expected = {counterexample.expected_output!r}\n"
                f"    assert normalize_path(value) == expected\n"
            )
            rules.append(MMinusRule(
                rule_id=rule_id,
                source_counterexample_id=counterexample.counterexample_id,
                claim_id=counterexample.claim_id,
                failure_pattern=(
                    f"mutant {counterexample.mutant_id} returned {counterexample.observed_output!r} "
                    f"for {counterexample.minimized_input!r} instead of {counterexample.expected_output!r}"
                ),
                correction_principle="Preserve the declared claim and add a regression test before any implementation change.",
                regression_test_candidate=test_name,
            ))
            tests.append(test_source)
        return MMinusCompilation(rules=tuple(rules), generated_tests=tuple(tests))
