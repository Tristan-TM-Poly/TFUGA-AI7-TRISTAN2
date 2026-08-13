from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Mapping, Sequence
import argparse
import json

from .github_memory import _stable_digest

R05_SCHEMA_VERSION = "0.5.0"
_EXECUTION_STATES = {"NOT_EXECUTED", "COMPLETED", "FAILED_TO_RUN"}
_INTERFACE_STATES = {"PASS", "FAIL", "UNKNOWN"}
_VERDICTS = {"COMPATIBLE", "PARTIAL_COMPATIBLE", "INCOMPATIBLE", "UNKNOWN"}


def _dedupe(values: Sequence[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    if total <= 0:
        return None
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = (
        z
        * sqrt((p * (1.0 - p) / total) + (z * z) / (4.0 * total * total))
        / denom
    )
    return round(max(0.0, center - half), 6), round(min(1.0, center + half), 6)


@dataclass(frozen=True)
class InterfaceCheck:
    name: str
    status: str
    evidence_ref: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InterfaceCheck":
        status = str(payload.get("status") or "UNKNOWN").upper()
        if status not in _INTERFACE_STATES:
            raise ValueError(f"unsupported interface status: {status}")
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValueError("interface check requires name")
        return cls(
            name=name,
            status=status,
            evidence_ref=str(payload.get("evidence_ref") or "") or None,
        )


@dataclass(frozen=True)
class CompatibilityOutcomeReceipt:
    experiment_id: str
    candidate_ref: str
    candidate_head_sha: str | None
    target_ref: str
    target_head_sha: str | None
    execution_status: str
    execution_authority_ref: str | None
    isolation_receipt_ref: str | None
    tests_executed: int
    tests_passed: int
    tests_failed: int
    test_pass_rate: float | None
    test_pass_rate_wilson_95: tuple[float, float] | None
    interface_checks: tuple[InterfaceCheck, ...]
    residual_coverage: float
    regressions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    environment_fingerprint: str | None
    candidate_sha_fresh: bool
    target_sha_fresh: bool
    evidence_complete_for_promotion: bool
    verdict: str
    action_candidate: str
    memory_candidate: str
    action_authorized: bool
    memory_promotion_authorized: bool
    source_mutation_performed: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["interface_checks"] = [asdict(row) for row in self.interface_checks]
        return payload


@dataclass(frozen=True)
class OutcomeInput:
    experiment_id: str
    candidate_ref: str
    candidate_head_sha: str | None
    target_head_sha: str | None
    execution_status: str
    execution_authority_ref: str | None
    isolation_receipt_ref: str | None
    tests_executed: int
    tests_passed: int
    tests_failed: int
    interface_checks: tuple[InterfaceCheck, ...]
    residual_coverage: float
    regressions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    environment_fingerprint: str | None
    source_mutation_performed: bool

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OutcomeInput":
        status = str(payload.get("execution_status") or "NOT_EXECUTED").upper()
        if status not in _EXECUTION_STATES:
            raise ValueError(f"unsupported execution status: {status}")
        tests_executed = int(payload.get("tests_executed", 0))
        tests_passed = int(payload.get("tests_passed", 0))
        tests_failed = int(payload.get("tests_failed", 0))
        if min(tests_executed, tests_passed, tests_failed) < 0:
            raise ValueError("test counts must be non-negative")
        if tests_passed + tests_failed != tests_executed:
            raise ValueError("tests_passed + tests_failed must equal tests_executed")
        coverage = float(payload.get("residual_coverage", 0.0))
        if not 0.0 <= coverage <= 1.0:
            raise ValueError("residual_coverage must be in [0,1]")
        return cls(
            experiment_id=str(payload.get("experiment_id") or ""),
            candidate_ref=str(payload.get("candidate_ref") or ""),
            candidate_head_sha=str(payload.get("candidate_head_sha") or "") or None,
            target_head_sha=str(payload.get("target_head_sha") or "") or None,
            execution_status=status,
            execution_authority_ref=str(payload.get("execution_authority_ref") or "") or None,
            isolation_receipt_ref=str(payload.get("isolation_receipt_ref") or "") or None,
            tests_executed=tests_executed,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            interface_checks=tuple(
                InterfaceCheck.from_dict(row)
                for row in payload.get("interface_checks", [])
                if isinstance(row, Mapping)
            ),
            residual_coverage=coverage,
            regressions=_dedupe(tuple(map(str, payload.get("regressions", [])))),
            evidence_refs=_dedupe(tuple(map(str, payload.get("evidence_refs", [])))),
            environment_fingerprint=str(payload.get("environment_fingerprint") or "") or None,
            source_mutation_performed=bool(payload.get("source_mutation_performed", False)),
        )


def _contract_map(r04_report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if str(r04_report.get("schema") or "") != "omega-pr-5k2n-compatibility-inspection/v0.4.0":
        raise ValueError("R0.5 requires an R0.4 compatibility-inspection report")
    return {
        str(row.get("experiment_id")): row
        for row in r04_report.get("compatibility_experiment_contracts", [])
        if isinstance(row, Mapping) and row.get("experiment_id")
    }


def pending_outcome_inputs(r04_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    contracts = _contract_map(r04_report)
    rows: list[dict[str, Any]] = []
    for experiment_id, contract in sorted(contracts.items()):
        rows.append(
            {
                "experiment_id": experiment_id,
                "candidate_ref": contract.get("candidate_ref"),
                "candidate_head_sha": contract.get("candidate_head_sha"),
                "target_head_sha": contract.get("target_head_sha"),
                "execution_status": "NOT_EXECUTED",
                "execution_authority_ref": None,
                "isolation_receipt_ref": None,
                "tests_executed": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "interface_checks": [],
                "residual_coverage": 0.0,
                "regressions": [],
                "evidence_refs": [],
                "environment_fingerprint": None,
                "source_mutation_performed": False,
            }
        )
    return rows


def _classify(
    inp: OutcomeInput,
    contract: Mapping[str, Any],
) -> tuple[bool, bool, bool, str, str, str]:
    expected_candidate_sha = str(contract.get("candidate_head_sha") or "") or None
    expected_target_sha = str(contract.get("target_head_sha") or "") or None
    candidate_fresh = bool(expected_candidate_sha and inp.candidate_head_sha == expected_candidate_sha)
    target_fresh = bool(expected_target_sha and inp.target_head_sha == expected_target_sha)

    authority_complete = bool(inp.execution_authority_ref and inp.isolation_receipt_ref)
    evidence_complete = bool(inp.evidence_refs and inp.environment_fingerprint)
    interface_states = tuple(row.status for row in inp.interface_checks)
    interface_fail = any(state == "FAIL" for state in interface_states)
    interface_unknown = not interface_states or any(state == "UNKNOWN" for state in interface_states)
    interface_all_pass = bool(interface_states) and all(state == "PASS" for state in interface_states)

    promotable_evidence = (
        inp.execution_status == "COMPLETED"
        and candidate_fresh
        and target_fresh
        and authority_complete
        and evidence_complete
        and not inp.source_mutation_performed
        and inp.tests_executed > 0
        and not interface_unknown
    )

    if not promotable_evidence:
        return candidate_fresh, target_fresh, False, "UNKNOWN", "HOLD", "M_QUERY_CANDIDATE"

    if inp.tests_failed > 0 or interface_fail or inp.regressions:
        return candidate_fresh, target_fresh, True, "INCOMPATIBLE", "REJECT_CANDIDATE", "M_MINUS_CANDIDATE"

    if inp.tests_passed == inp.tests_executed and interface_all_pass and inp.residual_coverage >= 1.0:
        return candidate_fresh, target_fresh, True, "COMPATIBLE", "REUSE_CANDIDATE", "M_PLUS_CANDIDATE"

    if inp.tests_passed == inp.tests_executed and interface_all_pass and 0.0 < inp.residual_coverage < 1.0:
        return candidate_fresh, target_fresh, True, "PARTIAL_COMPATIBLE", "EXTEND_CANDIDATE", "M_QUERY_CANDIDATE"

    return candidate_fresh, target_fresh, True, "UNKNOWN", "HOLD", "M_QUERY_CANDIDATE"


def compile_compatibility_outcomes_r05(
    r04_report: Mapping[str, Any],
    outcomes: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    contracts = _contract_map(r04_report)
    raw_outcomes = list(outcomes) if outcomes is not None else pending_outcome_inputs(r04_report)

    seen: set[str] = set()
    receipts: list[CompatibilityOutcomeReceipt] = []
    for raw in raw_outcomes:
        inp = OutcomeInput.from_dict(raw)
        if not inp.experiment_id or inp.experiment_id not in contracts:
            raise ValueError(f"outcome references unknown experiment_id: {inp.experiment_id}")
        if inp.experiment_id in seen:
            raise ValueError(f"duplicate outcome for experiment_id: {inp.experiment_id}")
        seen.add(inp.experiment_id)
        contract = contracts[inp.experiment_id]
        expected_ref = str(contract.get("candidate_ref") or "")
        if inp.candidate_ref != expected_ref:
            raise ValueError("candidate_ref does not match CompatibilityExperimentContract")
        if inp.source_mutation_performed:
            # Compatibility court must remain observational with respect to candidate/target source.
            raise ValueError("source_mutation_performed must remain false in R0.5 compatibility outcomes")

        candidate_fresh, target_fresh, evidence_complete, verdict, action, memory = _classify(inp, contract)
        interval = _wilson_interval(inp.tests_passed, inp.tests_executed)
        pass_rate = round(inp.tests_passed / inp.tests_executed, 6) if inp.tests_executed else None
        receipt = CompatibilityOutcomeReceipt(
            experiment_id=inp.experiment_id,
            candidate_ref=inp.candidate_ref,
            candidate_head_sha=inp.candidate_head_sha,
            target_ref=str(contract.get("target_ref") or ""),
            target_head_sha=inp.target_head_sha,
            execution_status=inp.execution_status,
            execution_authority_ref=inp.execution_authority_ref,
            isolation_receipt_ref=inp.isolation_receipt_ref,
            tests_executed=inp.tests_executed,
            tests_passed=inp.tests_passed,
            tests_failed=inp.tests_failed,
            test_pass_rate=pass_rate,
            test_pass_rate_wilson_95=interval,
            interface_checks=inp.interface_checks,
            residual_coverage=round(inp.residual_coverage, 6),
            regressions=inp.regressions,
            evidence_refs=inp.evidence_refs,
            environment_fingerprint=inp.environment_fingerprint,
            candidate_sha_fresh=candidate_fresh,
            target_sha_fresh=target_fresh,
            evidence_complete_for_promotion=evidence_complete,
            verdict=verdict,
            action_candidate=action,
            memory_candidate=memory,
            action_authorized=False,
            memory_promotion_authorized=False,
            source_mutation_performed=False,
            boundary=(
                "CompatibilityOutcomeReceipt classifies supplied evidence under an exact experiment contract. "
                "A compatible verdict is still a review candidate, not automatic reuse authority; test counts and Wilson intervals are not truth probabilities."
            ),
        )
        if receipt.verdict not in _VERDICTS:
            raise AssertionError("internal verdict outside R0.5 verdict set")
        receipts.append(receipt)

    receipts.sort(
        key=lambda row: (
            {"COMPATIBLE": 0, "PARTIAL_COMPATIBLE": 1, "INCOMPATIBLE": 2, "UNKNOWN": 3}[row.verdict],
            -row.residual_coverage,
            -row.tests_executed,
            row.candidate_ref,
        )
    )
    verdict_counts = {name: sum(row.verdict == name for row in receipts) for name in sorted(_VERDICTS)}
    memory_counts = {
        name: sum(row.memory_candidate == name for row in receipts)
        for name in ("M_PLUS_CANDIDATE", "M_MINUS_CANDIDATE", "M_QUERY_CANDIDATE")
    }
    payload: dict[str, Any] = {
        "schema": f"omega-pr-5k2n-compatibility-outcomes/v{R05_SCHEMA_VERSION}",
        "source_r04_fingerprint": r04_report.get("fingerprint"),
        "experiment_contract_count": len(contracts),
        "outcome_receipt_count": len(receipts),
        "missing_outcome_contract_ids": sorted(set(contracts) - seen),
        "receipts": [row.to_dict() for row in receipts],
        "verdict_counts": verdict_counts,
        "memory_candidate_counts": memory_counts,
        "review_order": [row.experiment_id for row in receipts],
        "automatic_reuse_authorized": False,
        "automatic_memory_promotion_authorized": False,
        "write_authority_granted": False,
        "automatic_commit_allowed": False,
        "automatic_merge_allowed": False,
        "source_renderer_authorized": False,
        "oak_boundaries": [
            "CompatibilityOutcomeReceipt != automatic reuse authority",
            "test pass rate != probability of semantic compatibility",
            "Wilson interval over test cases != scientific confidence interval for truth",
            "COMPATIBLE != universally reusable",
            "PARTIAL_COMPATIBLE != complete residual coverage",
            "INCOMPATIBLE is scoped to the exact candidate/target/environment evidence",
            "UNKNOWN must remain HOLD",
            "stale candidate or target SHA blocks promotion",
            "completed execution without authority/isolation/evidence refs blocks promotion",
            "M_PLUS_CANDIDATE != canonical M+",
            "M_MINUS_CANDIDATE != canonical M- until reviewed and persisted",
            "source rendering remains separately authorized",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile evidence-bound Omega PR 5K2N R0.5 compatibility outcomes."
    )
    parser.add_argument("input")
    parser.add_argument("--output", default="-")
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must be an object")
    report = compile_compatibility_outcomes_r05(
        payload.get("r04_report", {}),
        payload.get("outcomes") if "outcomes" in payload else None,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(encoded, end="")
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
