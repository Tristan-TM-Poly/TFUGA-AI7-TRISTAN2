from __future__ import annotations

from typing import Any, Mapping, Sequence

from .behaviors import resolve_behavior
from .models import MetamorphicContract, MetamorphicFinding, MetamorphicReport


def contracts_from_mapping(raw: Mapping[str, Any]) -> tuple[MetamorphicContract, ...]:
    return tuple(
        MetamorphicContract(
            property_id=str(item["property_id"]),
            claim_id=str(item["claim_id"]),
            kind=str(item["kind"]),
            description=str(item["description"]),
            seed_inputs=tuple(str(value) for value in item.get("seed_inputs", [])),
        )
        for item in raw.get("contracts", [])
    )


def _evaluate(kind: str, behavior, value: str) -> tuple[bool, str, str]:
    observed = behavior(value)
    if kind == "exact_one_prefix_removal":
        expected = value[2:] if value.startswith("./") else value
        return observed == expected, f"output == {expected!r}", observed
    if kind == "leading_dot_preservation":
        required = value.startswith(".") and not value.startswith("./")
        passed = (not required) or observed.startswith(".")
        return passed, "leading non-relative dot is preserved", observed
    if kind == "ordinary_path_stability":
        required = not value.startswith("./")
        passed = (not required) or observed == value
        return passed, "ordinary path remains unchanged", observed
    if kind == "suffix_preservation":
        suffix = value.split("/")[-1]
        return observed.endswith(suffix), f"output ends with {suffix!r}", observed
    raise ValueError(f"unsupported metamorphic kind: {kind}")


class MetamorphicEngine:
    def evaluate(self, contracts: Sequence[MetamorphicContract], behaviors: Sequence[str]) -> MetamorphicReport:
        if not contracts:
            raise ValueError("at least one contract is required")
        findings: list[MetamorphicFinding] = []
        passed_checks = 0
        failed_checks = 0
        for behavior_name in sorted(set(behaviors)):
            behavior = resolve_behavior(behavior_name)
            for contract in sorted(contracts, key=lambda item: item.property_id):
                for value in contract.seed_inputs:
                    passed, relation, observed = _evaluate(contract.kind, behavior, value)
                    if passed:
                        passed_checks += 1
                    else:
                        failed_checks += 1
                        findings.append(MetamorphicFinding(
                            property_id=contract.property_id,
                            behavior=behavior_name,
                            input_value=value,
                            expected_relation=relation,
                            observed=observed,
                            severity="high" if contract.kind in {"exact_one_prefix_removal", "leading_dot_preservation"} else "medium",
                        ))
        return MetamorphicReport(
            contracts_evaluated=len(contracts),
            behaviors_evaluated=tuple(sorted(set(behaviors))),
            findings=tuple(findings),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
        )
