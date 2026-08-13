from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .core import stable_digest
from .external import ExternalActionRequest
from .normalizers import (
    ProviderResponseNormalizationError,
    ResponseContract,
    normalize_provider_response,
)

DRIFT_SCHEMA_VERSION = "0.6.0"
_EXPECTATIONS = {"SURVIVE", "REJECT", "FAILURE_RECEIPT", "DETECT"}
_SOURCE_KINDS = {"captured_sanitized", "contract_synthetic"}


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _path_parts(path: str) -> list[str]:
    normalized = path[2:] if path.startswith("$.") else path
    return [part for part in normalized.split(".") if part]


def _path_get(root: Any, path: str) -> Any:
    current = root
    for part in _path_parts(path):
        if isinstance(current, Mapping):
            if part not in current:
                raise KeyError(path)
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def _path_set(root: Any, path: str, value: Any) -> None:
    parts = _path_parts(path)
    if not parts:
        raise ValueError("cannot set root path")
    current = root
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(path)
    last = parts[-1]
    if isinstance(current, dict):
        current[last] = value
    elif isinstance(current, list):
        current[int(last)] = value
    else:
        raise KeyError(path)


def _path_delete(root: Any, path: str) -> None:
    parts = _path_parts(path)
    if not parts:
        raise ValueError("cannot delete root path")
    current = root
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(path)
    last = parts[-1]
    if isinstance(current, dict):
        del current[last]
    elif isinstance(current, list):
        del current[int(last)]
    else:
        raise KeyError(path)


def _first_selector(selector: str | Sequence[str]) -> str:
    if isinstance(selector, str):
        return selector
    values = tuple(map(str, selector))
    if not values:
        raise ValueError("selector sequence cannot be empty")
    return values[0]


@dataclass(frozen=True)
class DriftFixture:
    fixture_id: str
    provider: str
    source_kind: str
    source_fidelity: str
    request: ExternalActionRequest
    contract: ResponseContract
    raw_response: Any
    provenance: Mapping[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DriftFixture":
        source_kind = str(payload.get("source_kind", "contract_synthetic"))
        if source_kind not in _SOURCE_KINDS:
            raise ValueError(f"unknown fixture source_kind: {source_kind}")

        request_payload = payload["request"]
        if not isinstance(request_payload, Mapping):
            raise TypeError("fixture request must be an object")
        expected_outputs = tuple(map(str, request_payload.get("expected_outputs", [])))
        request = ExternalActionRequest(
            request_id=str(
                request_payload.get(
                    "request_id",
                    f"FIX-{stable_digest(payload)[:20].upper()}",
                )
            ),
            capability_id=str(request_payload["capability_id"]),
            connector=str(request_payload["connector"]),
            action=str(request_payload["action"]),
            authority=str(request_payload.get("authority", "read")),
            external_authority=str(request_payload.get("external_authority", "read")),
            arguments=dict(request_payload.get("arguments", {})),
            expected_outputs=expected_outputs,
            candidate_sha=(
                str(request_payload["candidate_sha"])
                if request_payload.get("candidate_sha") is not None
                else None
            ),
            plan_fingerprint=(
                str(request_payload["plan_fingerprint"])
                if request_payload.get("plan_fingerprint") is not None
                else None
            ),
        )

        contract_payload = payload["contract"]
        if not isinstance(contract_payload, Mapping):
            raise TypeError("fixture contract must be an object")
        contract = ResponseContract(
            provider=str(payload["provider"]),
            output_paths=dict(contract_payload.get("output_paths", {})),
            candidate_sha_paths=tuple(
                map(str, contract_payload.get("candidate_sha_paths", []))
            ),
            source_paths=tuple(map(str, contract_payload.get("source_paths", []))),
            mutation_ref_paths=tuple(
                map(str, contract_payload.get("mutation_ref_paths", []))
            ),
            require_candidate_sha=bool(
                contract_payload.get("require_candidate_sha", True)
            ),
        )
        contract.validate_for(request)

        return cls(
            fixture_id=str(payload["fixture_id"]),
            provider=str(payload["provider"]),
            source_kind=source_kind,
            source_fidelity=str(payload.get("source_fidelity", "unspecified")),
            request=request,
            contract=contract,
            raw_response=_deepcopy(payload["raw_response"]),
            provenance=dict(payload.get("provenance", {})),
        )


@dataclass(frozen=True)
class DriftCase:
    case_id: str
    family: str
    expectation: str
    raw_response: Any
    note: str

    def __post_init__(self) -> None:
        if self.expectation not in _EXPECTATIONS:
            raise ValueError(f"unknown drift expectation: {self.expectation}")


def load_fixture_corpus(payload: Mapping[str, Any]) -> tuple[DriftFixture, ...]:
    return tuple(DriftFixture.from_dict(item) for item in payload.get("fixtures", []))


def _identity_body(raw: Any) -> tuple[dict[str, Any], Any]:
    if not isinstance(raw, Mapping):
        return {}, _deepcopy(raw)
    identity: dict[str, Any] = {}
    for key in ("connector_name", "action_name"):
        if key in raw:
            identity[key] = raw[key]
    body = {
        key: _deepcopy(value)
        for key, value in raw.items()
        if key not in identity
    }
    return identity, body


def _output_paths(fixture: DriftFixture) -> list[str]:
    return [
        _first_selector(fixture.contract.output_paths[name])
        for name in fixture.request.expected_outputs
    ]


def _mutate_first_output(fixture: DriftFixture, raw: Any, *, mode: str) -> Any:
    mutated = _deepcopy(raw)
    paths = _output_paths(fixture)
    if not paths:
        return mutated
    path = paths[0]
    if mode == "drop":
        _path_delete(mutated, path)
    elif mode == "null":
        _path_set(mutated, path, None)
    elif mode == "wrong_type":
        current = _path_get(mutated, path)
        replacement = [] if not isinstance(current, list) else {"drift": True}
        _path_set(mutated, path, replacement)
    elif mode == "semantic_change":
        current = _path_get(mutated, path)
        if isinstance(current, str):
            _path_set(mutated, path, current + "-drift")
        elif isinstance(current, bool):
            _path_set(mutated, path, not current)
        elif isinstance(current, (int, float)):
            _path_set(mutated, path, current + 1)
        elif isinstance(current, Mapping):
            replacement = dict(current)
            replacement["drift_field"] = True
            _path_set(mutated, path, replacement)
        elif isinstance(current, list):
            replacement = list(current)
            replacement.append({"drift": True})
            _path_set(mutated, path, replacement)
        else:
            _path_set(mutated, path, "drift")
    else:
        raise ValueError(mode)
    return mutated


def generate_drift_cases(fixture: DriftFixture) -> tuple[DriftCase, ...]:
    raw = _deepcopy(fixture.raw_response)
    identity, body = _identity_body(raw)
    cases: list[DriftCase] = []

    def add(
        case_id: str,
        family: str,
        expectation: str,
        payload: Any,
        note: str,
    ) -> None:
        cases.append(
            DriftCase(
                case_id=f"{fixture.fixture_id}:{case_id}",
                family=family,
                expectation=expectation,
                raw_response=payload,
                note=note,
            )
        )

    add(
        "baseline",
        "baseline",
        "SURVIVE",
        _deepcopy(raw),
        "Unmodified sanitized fixture.",
    )

    for index in range(1, 4):
        noisy = _deepcopy(raw)
        if isinstance(noisy, dict):
            noisy[f"provider_drift_meta_{index}"] = {
                "schema_hint": f"future-{index}",
                "ignored": True,
            }
        add(
            f"additive-metadata-{index}",
            "benign",
            "SURVIVE",
            noisy,
            "Unknown additive metadata must not break normalization.",
        )

    without_identity = _deepcopy(raw)
    if isinstance(without_identity, dict):
        without_identity.pop("connector_name", None)
        without_identity.pop("action_name", None)
    add(
        "identity-omitted",
        "benign",
        "SURVIVE",
        without_identity,
        "Identity metadata is optional when absent.",
    )

    result_json = dict(identity)
    result_json["result"] = json.dumps(body, sort_keys=True)
    add(
        "result-json-wrapper",
        "wrapper",
        "SURVIVE",
        result_json,
        "JSON result envelope should unwrap.",
    )

    structured = dict(identity)
    structured["structuredContent"] = _deepcopy(body)
    add(
        "structured-content-wrapper",
        "wrapper",
        "SURVIVE",
        structured,
        "structuredContent envelope should unwrap.",
    )

    content_json = dict(identity)
    content_json["content"] = json.dumps(body, sort_keys=True)
    add(
        "content-json-wrapper",
        "wrapper",
        "SURVIVE",
        content_json,
        "JSON content envelope should unwrap.",
    )

    nested = dict(identity)
    nested["result"] = json.dumps({"structuredContent": body}, sort_keys=True)
    add(
        "nested-result-structured",
        "wrapper",
        "SURVIVE",
        nested,
        "Nested result->structuredContent drift should unwrap.",
    )

    mismatch_connector = _deepcopy(raw)
    if isinstance(mismatch_connector, dict):
        mismatch_connector["connector_name"] = "WrongProvider"
    add(
        "connector-mismatch",
        "identity",
        "REJECT",
        mismatch_connector,
        "Contradictory connector identity must fail closed.",
    )

    mismatch_action = _deepcopy(raw)
    if isinstance(mismatch_action, dict):
        mismatch_action["action_name"] = f"{fixture.request.action}__drift"
    add(
        "action-mismatch",
        "identity",
        "REJECT",
        mismatch_action,
        "Contradictory action identity must fail closed.",
    )

    error_envelope = _deepcopy(raw)
    if isinstance(error_envelope, dict):
        error_envelope["is_error"] = True
        error_envelope["error"] = {"message": "sanitized provider failure"}
    add(
        "provider-error",
        "error",
        "FAILURE_RECEIPT",
        error_envelope,
        "Provider error must become typed FAILURE.",
    )

    try:
        add(
            "required-output-dropped",
            "output",
            "REJECT",
            _mutate_first_output(fixture, raw, mode="drop"),
            "Missing required output must be rejected.",
        )
        add(
            "required-output-null",
            "semantic",
            "DETECT",
            _mutate_first_output(fixture, raw, mode="null"),
            "Null required output must be detected as degradation or rejection.",
        )
        add(
            "required-output-wrong-type",
            "semantic",
            "DETECT",
            _mutate_first_output(fixture, raw, mode="wrong_type"),
            "Required output type drift must be detected.",
        )
        add(
            "required-output-semantic-change",
            "semantic",
            "DETECT",
            _mutate_first_output(fixture, raw, mode="semantic_change"),
            "Required output semantic drift must change the normalized signature.",
        )
    except (KeyError, IndexError, ValueError):
        pass

    if fixture.request.candidate_sha and fixture.contract.candidate_sha_paths:
        sha_path = fixture.contract.candidate_sha_paths[0]
        stale = _deepcopy(raw)
        try:
            _path_set(
                stale,
                sha_path,
                f"{fixture.request.candidate_sha}-stale",
            )
            add(
                "candidate-sha-stale",
                "freshness",
                "REJECT",
                stale,
                "Stale candidate SHA must fail closed.",
            )
        except (KeyError, IndexError, ValueError):
            pass

    for left in range(1, 4):
        for right in range(left + 1, 4):
            pair = _deepcopy(raw)
            if isinstance(pair, dict):
                pair[f"provider_drift_meta_{left}"] = {
                    "schema_hint": f"future-{left}",
                    "ignored": True,
                }
                pair[f"provider_drift_meta_{right}"] = {
                    "schema_hint": f"future-{right}",
                    "ignored": True,
                }
            add(
                f"pair-additive-{left}-{right}",
                "pairwise-benign",
                "SURVIVE",
                pair,
                "Second-order additive schema drift must preserve receipt fidelity.",
            )

    return tuple(cases)


def _receipt_signature(receipt: Any) -> dict[str, Any]:
    return {
        "status": receipt.status,
        "outputs": dict(receipt.outputs),
        "observed_candidate_sha": receipt.observed_candidate_sha,
        "mutation_performed": receipt.mutation_performed,
    }


def _expectation_satisfied(expectation: str, actual: str) -> bool:
    if expectation == "DETECT":
        return actual in {"DEGRADED", "REJECT"}
    return expectation == actual


def _run_case(
    fixture: DriftFixture,
    case: DriftCase,
    baseline_signature: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        receipt = normalize_provider_response(
            fixture.request,
            case.raw_response,
            fixture.contract,
            notes=(f"drift_case={case.case_id}",),
        )
        signature = _receipt_signature(receipt)
        if receipt.status == "FAILURE":
            actual = "FAILURE_RECEIPT"
        elif signature == baseline_signature:
            actual = "SURVIVE"
        else:
            actual = "DEGRADED"
        error = None
    except ProviderResponseNormalizationError as exc:
        signature = None
        actual = "REJECT"
        error = str(exc)

    correct = _expectation_satisfied(case.expectation, actual)
    return {
        "case_id": case.case_id,
        "family": case.family,
        "expected": case.expectation,
        "actual": actual,
        "correct": correct,
        "note": case.note,
        "error": error,
        "receipt_signature": signature,
    }


def benchmark_fixture(fixture: DriftFixture) -> dict[str, Any]:
    baseline_receipt = normalize_provider_response(
        fixture.request,
        fixture.raw_response,
        fixture.contract,
        notes=(f"fixture={fixture.fixture_id}",),
    )
    if baseline_receipt.status != "SUCCESS":
        raise ProviderResponseNormalizationError(
            f"fixture {fixture.fixture_id} baseline is not SUCCESS"
        )

    baseline_signature = _receipt_signature(baseline_receipt)
    cases = generate_drift_cases(fixture)
    results = [
        _run_case(fixture, case, baseline_signature)
        for case in cases
    ]
    mismatches = [item for item in results if not item["correct"]]
    benign = [
        item
        for item in results
        if item["expected"] == "SURVIVE"
    ]
    breaking = [
        item
        for item in results
        if item["expected"] in {"REJECT", "DETECT"}
    ]
    detected_breaking = [
        item
        for item in breaking
        if item["actual"] in {"REJECT", "DEGRADED"}
    ]

    drift_findings = [
        {
            "kind": "schema_drift_observation",
            "fixture_id": fixture.fixture_id,
            "case_id": item["case_id"],
            "expected": item["expected"],
            "actual": item["actual"],
            "classification": (
                "M_MINUS_CANDIDATE"
                if item["actual"] in {"DEGRADED", "REJECT"}
                else "COURT"
            ),
        }
        for item in results
        if item["actual"] != "SURVIVE"
    ]

    return {
        "schema": "omega-capability-drift-fixture-report/v1",
        "fixture_id": fixture.fixture_id,
        "provider": fixture.provider,
        "source_kind": fixture.source_kind,
        "source_fidelity": fixture.source_fidelity,
        "fixture_fingerprint": stable_digest(fixture.raw_response),
        "case_count": len(results),
        "correct_count": len(results) - len(mismatches),
        "mismatch_count": len(mismatches),
        "classification_accuracy": (
            (len(results) - len(mismatches)) / len(results)
            if results
            else 1.0
        ),
        "benign_survival_rate": (
            sum(item["actual"] == "SURVIVE" for item in benign) / len(benign)
            if benign
            else 1.0
        ),
        "breaking_detection_rate": (
            len(detected_breaking) / len(breaking)
            if breaking
            else 1.0
        ),
        "baseline_signature": baseline_signature,
        "cases": results,
        "drift_findings": drift_findings,
        "classification_mismatches": mismatches,
    }


def benchmark_fixture_corpus(
    fixtures: Sequence[DriftFixture],
) -> dict[str, Any]:
    reports = [benchmark_fixture(fixture) for fixture in fixtures]
    providers: dict[str, dict[str, Any]] = {}

    for report in reports:
        row = providers.setdefault(
            report["provider"],
            {
                "fixtures": 0,
                "cases": 0,
                "correct": 0,
                "mismatches": 0,
                "breaking_cases": 0,
                "breaking_detected": 0,
            },
        )
        row["fixtures"] += 1
        row["cases"] += report["case_count"]
        row["correct"] += report["correct_count"]
        row["mismatches"] += report["mismatch_count"]

        for case in report["cases"]:
            if case["expected"] in {"REJECT", "DETECT"}:
                row["breaking_cases"] += 1
                if case["actual"] in {"REJECT", "DEGRADED"}:
                    row["breaking_detected"] += 1

    for row in providers.values():
        row["classification_accuracy"] = (
            row["correct"] / row["cases"]
            if row["cases"]
            else 1.0
        )
        row["breaking_detection_rate"] = (
            row["breaking_detected"] / row["breaking_cases"]
            if row["breaking_cases"]
            else 1.0
        )

    total_cases = sum(report["case_count"] for report in reports)
    total_mismatches = sum(report["mismatch_count"] for report in reports)
    captured = sum(
        report["source_kind"] == "captured_sanitized"
        for report in reports
    )
    synthetic = sum(
        report["source_kind"] == "contract_synthetic"
        for report in reports
    )
    all_breaking = [
        case
        for report in reports
        for case in report["cases"]
        if case["expected"] in {"REJECT", "DETECT"}
    ]
    detected_breaking = [
        case
        for case in all_breaking
        if case["actual"] in {"REJECT", "DEGRADED"}
    ]

    return {
        "schema": "omega-capability-schema-drift-report/v1",
        "version": DRIFT_SCHEMA_VERSION,
        "status": "PASS" if total_mismatches == 0 else "FAIL",
        "fixture_count": len(reports),
        "captured_sanitized_fixture_count": captured,
        "contract_synthetic_fixture_count": synthetic,
        "case_count": total_cases,
        "correct_count": total_cases - total_mismatches,
        "mismatch_count": total_mismatches,
        "classification_accuracy": (
            (total_cases - total_mismatches) / total_cases
            if total_cases
            else 1.0
        ),
        "breaking_detection_rate": (
            len(detected_breaking) / len(all_breaking)
            if all_breaking
            else 1.0
        ),
        "providers": dict(sorted(providers.items())),
        "fixtures": reports,
        "m_minus_candidates": [
            finding
            for report in reports
            for finding in report["drift_findings"]
            if finding["classification"] == "M_MINUS_CANDIDATE"
        ],
        "classification_mismatches": [
            mismatch
            for report in reports
            for mismatch in report["classification_mismatches"]
        ],
    }


def load_fixture_corpus_file(
    path: str | Path,
) -> tuple[DriftFixture, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError("fixture corpus must be a JSON object")
    return load_fixture_corpus(payload)


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(
            "usage: python -m omega_capability_os_t.drift <fixture-corpus.json>",
            file=sys.stderr,
        )
        return 2

    report = benchmark_fixture_corpus(
        load_fixture_corpus_file(args[0])
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
