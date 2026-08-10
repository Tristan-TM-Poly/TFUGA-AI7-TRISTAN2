from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

MUTANT_STATUSES = ("KILLED", "SURVIVED", "EQUIVALENT", "INVALID")
FINDING_SEVERITIES = ("low", "medium", "high", "critical")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(str(value) for value in values)))


@dataclass(frozen=True)
class MutationSpec:
    mutant_id: str
    operator_id: str
    target: str
    behavior: str
    description: str
    weight: float = 1.0
    expected_equivalent: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mutant_id or not self.operator_id or not self.target:
            raise ValueError("mutant_id, operator_id and target are required")
        if self.weight <= 0:
            raise ValueError("mutant weight must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "metadata": dict(self.metadata)}


@dataclass(frozen=True)
class MutationTest:
    test_id: str
    claim_ids: tuple[str, ...]
    input_value: str
    expected_output: str
    evidence_kind: str = "unit"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["claim_ids"] = list(self.claim_ids)
        return payload


@dataclass(frozen=True)
class MutantResult:
    mutant_id: str
    operator_id: str
    status: str
    weight: float
    killed_by: tuple[str, ...]
    surviving_tests: tuple[str, ...]
    observed_outputs: Mapping[str, str]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in MUTANT_STATUSES:
            raise ValueError(f"unsupported mutant status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutant_id": self.mutant_id,
            "operator_id": self.operator_id,
            "status": self.status,
            "weight": self.weight,
            "killed_by": list(self.killed_by),
            "surviving_tests": list(self.surviving_tests),
            "observed_outputs": dict(sorted(self.observed_outputs.items())),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MutationCampaignReport:
    target: str
    baseline_behavior: str
    results: tuple[MutantResult, ...]
    generated: int
    evaluated: int
    killed: int
    survived: int
    equivalent: int
    invalid: int
    mutation_score: float
    weighted_mutation_score: float
    surviving_mutant_ids: tuple[str, ...]
    schema: str = "omega-ci-mutation-campaign/v5"

    @property
    def campaign_id(self) -> str:
        return f"MUTCAMP-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "baseline_behavior": self.baseline_behavior,
            "results": [item.to_dict() for item in self.results],
            "generated": self.generated,
            "evaluated": self.evaluated,
            "killed": self.killed,
            "survived": self.survived,
            "equivalent": self.equivalent,
            "invalid": self.invalid,
            "mutation_score": self.mutation_score,
            "weighted_mutation_score": self.weighted_mutation_score,
            "surviving_mutant_ids": list(self.surviving_mutant_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "campaign_id": self.campaign_id,
            **self.identity_payload(),
            "execution_authorized": False,
            "code_changes_applied": False,
            "automatic_patch_allowed": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class Counterexample:
    claim_id: str
    mutant_id: str
    property_id: str
    original_input: str
    minimized_input: str
    expected_output: str
    observed_output: str
    reduction_steps: tuple[str, ...]
    provenance: tuple[str, ...]

    @property
    def counterexample_id(self) -> str:
        return f"COUNTEREX-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "mutant_id": self.mutant_id,
            "property_id": self.property_id,
            "original_input": self.original_input,
            "minimized_input": self.minimized_input,
            "expected_output": self.expected_output,
            "observed_output": self.observed_output,
            "reduction_steps": list(self.reduction_steps),
            "provenance": list(self.provenance),
        }

    def to_dict(self) -> dict[str, Any]:
        return {"counterexample_id": self.counterexample_id, **self.identity_payload()}


@dataclass(frozen=True)
class CounterexampleReport:
    searched_mutant_ids: tuple[str, ...]
    counterexamples: tuple[Counterexample, ...]
    candidates_evaluated: int
    exhausted: bool
    schema: str = "omega-ci-counterexample-report/v5"

    @property
    def report_id(self) -> str:
        return f"COUNTERREPORT-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "searched_mutant_ids": list(self.searched_mutant_ids),
            "counterexamples": [item.to_dict() for item in self.counterexamples],
            "candidates_evaluated": self.candidates_evaluated,
            "exhausted": self.exhausted,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "report_id": self.report_id,
            **self.identity_payload(),
            "execution_authorized": False,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class MetamorphicContract:
    property_id: str
    claim_id: str
    kind: str
    description: str
    seed_inputs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["seed_inputs"] = list(self.seed_inputs)
        return payload


@dataclass(frozen=True)
class MetamorphicFinding:
    property_id: str
    behavior: str
    input_value: str
    expected_relation: str
    observed: str
    severity: str

    def __post_init__(self) -> None:
        if self.severity not in FINDING_SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetamorphicReport:
    contracts_evaluated: int
    behaviors_evaluated: tuple[str, ...]
    findings: tuple[MetamorphicFinding, ...]
    passed_checks: int
    failed_checks: int
    schema: str = "omega-ci-metamorphic-report/v5"

    @property
    def report_id(self) -> str:
        return f"METAMORPHIC-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "contracts_evaluated": self.contracts_evaluated,
            "behaviors_evaluated": list(self.behaviors_evaluated),
            "findings": [item.to_dict() for item in self.findings],
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload(), "remote_mutations": 0}


@dataclass(frozen=True)
class DifferentialDivergence:
    behavior: str
    input_value: str
    reference_output: str
    candidate_output: str
    claim_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DifferentialReport:
    reference_behavior: str
    candidate_behaviors: tuple[str, ...]
    corpus_size: int
    divergences: tuple[DifferentialDivergence, ...]
    agreements: int
    schema: str = "omega-ci-differential-report/v5"

    @property
    def report_id(self) -> str:
        return f"DIFF-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "reference_behavior": self.reference_behavior,
            "candidate_behaviors": list(self.candidate_behaviors),
            "corpus_size": self.corpus_size,
            "divergences": [item.to_dict() for item in self.divergences],
            "agreements": self.agreements,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "report_id": self.report_id, **self.identity_payload(), "remote_mutations": 0}


@dataclass(frozen=True)
class MMinusRule:
    rule_id: str
    source_counterexample_id: str
    claim_id: str
    failure_pattern: str
    correction_principle: str
    regression_test_candidate: str
    status: str = "GENERATED_CANDIDATE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MMinusCompilation:
    rules: tuple[MMinusRule, ...]
    generated_tests: tuple[str, ...]
    schema: str = "omega-ci-mminus-compilation/v5"

    @property
    def compilation_id(self) -> str:
        return f"MMINUSCOMP-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "rules": [item.to_dict() for item in self.rules],
            "generated_tests": list(self.generated_tests),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "compilation_id": self.compilation_id,
            **self.identity_payload(),
            "tests_applied": False,
            "code_changes_applied": False,
            "human_review_required": True,
            "remote_mutations": 0,
        }


@dataclass(frozen=True)
class EcologyAgentResult:
    agent: str
    niche: str
    budget: int
    findings: int
    artifacts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = list(self.artifacts)
        return payload


@dataclass(frozen=True)
class MutationEcologyReport:
    campaign_id: str
    counterexample_report_id: str
    metamorphic_report_id: str
    differential_report_id: str
    mminus_compilation_id: str
    agents: tuple[EcologyAgentResult, ...]
    unresolved_survivors: tuple[str, ...]
    proof_debt_delta: float
    schema: str = "omega-ci-mutation-ecology/v5"

    @property
    def ecology_id(self) -> str:
        return f"MUTECO-{stable_digest(self.identity_payload())[:20].upper()}"

    def identity_payload(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "counterexample_report_id": self.counterexample_report_id,
            "metamorphic_report_id": self.metamorphic_report_id,
            "differential_report_id": self.differential_report_id,
            "mminus_compilation_id": self.mminus_compilation_id,
            "agents": [item.to_dict() for item in self.agents],
            "unresolved_survivors": list(self.unresolved_survivors),
            "proof_debt_delta": self.proof_debt_delta,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ecology_id": self.ecology_id,
            **self.identity_payload(),
            "maximum_authority": "A3",
            "execution_authorized": False,
            "automatic_patch_allowed": False,
            "automatic_merge_allowed": False,
            "human_review_required": True,
            "remote_mutations": 0,
        }
