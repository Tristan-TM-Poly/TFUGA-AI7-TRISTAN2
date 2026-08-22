from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import inspect
import json
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable, Iterable, Mapping


COMPETITORS = ("MORPH_GENOME", "DOMAIN_SPECIFIC", "MINIMAL_DICT", "NO_ABSTRACTION")


@dataclass(frozen=True)
class TournamentCase:
    id: str
    domain: str
    record: Mapping[str, Any]
    required_keys: tuple[str, ...]
    evidence_keys: tuple[str, ...]
    regeneration_required: bool
    maintenance_mutations: tuple[Mapping[str, Any], ...]
    no_abstraction_supported: bool = False
    adversarial_for_morph_genome: bool = False


@dataclass(frozen=True)
class RepresentationResult:
    case_id: str
    domain: str
    competitor: str
    probe_completion: bool
    evidence_provenance_preservation: bool
    regeneration_closure: float
    mutation_detection: float
    implementation_source_lines: int
    serialized_bytes: int
    execution_steps: int
    adapter_failures: int
    future_work_eliminated: int
    maintenance_tasks: int
    median_latency_ns: int
    hard_gate_pass: bool
    reasons: tuple[str, ...]

    def stable_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("median_latency_ns", None)
        return payload


@dataclass(frozen=True)
class TournamentDecision:
    case_id: str
    winner: str | None
    valid_competitors: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class TournamentReport:
    corpus_sha256: str
    results: tuple[RepresentationResult, ...]
    decisions: tuple[TournamentDecision, ...]
    morph_genome_disposition: str
    validity_domain: str
    global_pass: bool = False
    external_action_performed: bool = False
    auto_promoted: bool = False

    def stable_digest(self) -> str:
        payload = {
            "corpus_sha256": self.corpus_sha256,
            "results": [result.stable_payload() for result in self.results],
            "decisions": [asdict(decision) for decision in self.decisions],
            "morph_genome_disposition": self.morph_genome_disposition,
            "validity_domain": self.validity_domain,
            "global_pass": self.global_pass,
            "external_action_performed": self.external_action_performed,
            "auto_promoted": self.auto_promoted,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_required(record: Mapping[str, Any], required_keys: Iterable[str]) -> None:
    missing = [key for key in required_keys if key not in record]
    if missing:
        raise ValueError("missing required keys: " + ",".join(sorted(missing)))


def _morph_encode(case: TournamentCase, record: Mapping[str, Any]) -> Mapping[str, Any]:
    _validate_required(record, case.required_keys)
    return {
        "id": str(record.get("id", case.id)),
        "purpose": str(record.get("purpose", record.get("goal", case.domain))),
        "operators": tuple(record.get("operators", record.get("actions", ()))),
        "constraints": tuple(record.get("constraints", ())),
        "evidence_contracts": tuple(record.get("evidence_contracts", case.evidence_keys)),
        "resources": tuple(record.get("resources", ())),
        "permissions": tuple(record.get("permissions", ())),
        "memory_refs": tuple(record.get("memory_refs", ())),
        "regeneration_rules": tuple(record.get("regeneration_rules", ())),
        "parent_ids": tuple(record.get("parent_ids", ())),
        "version": str(record.get("version", "0.1.0")),
        "domain_payload": deepcopy(dict(record)),
    }


def _morph_decode(_: TournamentCase, encoded: Mapping[str, Any]) -> Mapping[str, Any]:
    return deepcopy(dict(encoded["domain_payload"]))


def _domain_encode(case: TournamentCase, record: Mapping[str, Any]) -> Mapping[str, Any]:
    _validate_required(record, case.required_keys)
    return {"domain": case.domain, "record": deepcopy(dict(record))}


def _domain_decode(_: TournamentCase, encoded: Mapping[str, Any]) -> Mapping[str, Any]:
    return deepcopy(dict(encoded["record"]))


def _dict_encode(_: TournamentCase, record: Mapping[str, Any]) -> Mapping[str, Any]:
    return deepcopy(dict(record))


def _dict_decode(_: TournamentCase, encoded: Mapping[str, Any]) -> Mapping[str, Any]:
    return deepcopy(dict(encoded))


def _direct_encode(case: TournamentCase, record: Mapping[str, Any]) -> Mapping[str, Any]:
    if not case.no_abstraction_supported:
        raise ValueError("NO_ABSTRACTION is not defined for this frozen task")
    _validate_required(record, case.required_keys)
    return record


def _direct_decode(_: TournamentCase, encoded: Mapping[str, Any]) -> Mapping[str, Any]:
    return encoded


_ADAPTERS: dict[str, tuple[Callable[[TournamentCase, Mapping[str, Any]], Mapping[str, Any]], Callable[[TournamentCase, Mapping[str, Any]], Mapping[str, Any]], int]] = {
    "MORPH_GENOME": (_morph_encode, _morph_decode, 4),
    "DOMAIN_SPECIFIC": (_domain_encode, _domain_decode, 2),
    "MINIMAL_DICT": (_dict_encode, _dict_decode, 1),
    "NO_ABSTRACTION": (_direct_encode, _direct_decode, 0),
}


def _source_lines(fn: Callable[..., Any]) -> int:
    return sum(
        1
        for line in inspect.getsource(fn).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _canonical_bytes(value: Mapping[str, Any]) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=list).encode("utf-8"))


def _roundtrip(case: TournamentCase, competitor: str, record: Mapping[str, Any]) -> tuple[bool, int, int, int]:
    encode, decode, execution_steps = _ADAPTERS[competitor]
    failures = 0
    start = perf_counter_ns()
    try:
        encoded = encode(case, record)
        decoded = decode(case, encoded)
        completed = dict(decoded) == dict(record)
        size = _canonical_bytes(encoded)
    except (KeyError, TypeError, ValueError):
        failures = 1
        completed = False
        size = 0
    latency = perf_counter_ns() - start
    return completed, size, execution_steps, latency + failures * 0


def _mutation_detection(case: TournamentCase, competitor: str) -> tuple[float, int]:
    encode, _, _ = _ADAPTERS[competitor]
    if not case.required_keys:
        return 1.0, 0
    detected = 0
    failures = 0
    for key in case.required_keys:
        mutated = deepcopy(dict(case.record))
        mutated.pop(key, None)
        try:
            encode(case, mutated)
        except (KeyError, TypeError, ValueError):
            detected += 1
        except Exception:
            failures += 1
    return detected / len(case.required_keys), failures


def _maintenance_transfer(case: TournamentCase, competitor: str) -> tuple[int, int]:
    successes = 0
    failures = 0
    for mutation in case.maintenance_mutations:
        candidate = deepcopy(dict(case.record))
        candidate.update(deepcopy(dict(mutation)))
        completed, _, _, _ = _roundtrip(case, competitor, candidate)
        if completed:
            successes += 1
        else:
            failures += 1
    return successes, failures


def _evidence_preserved(case: TournamentCase, competitor: str) -> bool:
    completed, _, _, _ = _roundtrip(case, competitor, case.record)
    if not completed:
        return False
    encode, decode, _ = _ADAPTERS[competitor]
    try:
        decoded = decode(case, encode(case, case.record))
    except (KeyError, TypeError, ValueError):
        return False
    return all(decoded.get(key) == case.record.get(key) for key in case.evidence_keys)


def evaluate_case(case: TournamentCase, competitor: str) -> RepresentationResult:
    if competitor not in _ADAPTERS:
        raise ValueError(f"unknown competitor: {competitor}")
    completed, serialized_bytes, execution_steps, latency = _roundtrip(case, competitor, case.record)
    mutation_detection, mutation_failures = _mutation_detection(case, competitor)
    future_work_eliminated, maintenance_failures = _maintenance_transfer(case, competitor)
    evidence_preserved = _evidence_preserved(case, competitor)
    regeneration_closure = 1.0 if completed else 0.0
    if case.regeneration_required and not case.record.get("regeneration_rules"):
        regeneration_closure = 0.0

    reasons: list[str] = []
    if not completed:
        reasons.append("frozen probe did not complete")
    if not evidence_preserved:
        reasons.append("evidence/provenance was not preserved")
    if case.regeneration_required and regeneration_closure < 1.0:
        reasons.append("regeneration closure is incomplete")
    if mutation_detection < 1.0:
        reasons.append("required-key falsifier detection is incomplete")

    hard_gate_pass = (
        completed
        and evidence_preserved
        and (not case.regeneration_required or regeneration_closure == 1.0)
        and mutation_detection == 1.0
    )
    encode, decode, _ = _ADAPTERS[competitor]
    implementation_source_lines = _source_lines(encode) + _source_lines(decode)
    if competitor == "DOMAIN_SPECIFIC":
        implementation_source_lines += len(case.required_keys)

    return RepresentationResult(
        case_id=case.id,
        domain=case.domain,
        competitor=competitor,
        probe_completion=completed,
        evidence_provenance_preservation=evidence_preserved,
        regeneration_closure=regeneration_closure,
        mutation_detection=mutation_detection,
        implementation_source_lines=implementation_source_lines,
        serialized_bytes=serialized_bytes,
        execution_steps=execution_steps,
        adapter_failures=mutation_failures + maintenance_failures + (0 if completed else 1),
        future_work_eliminated=future_work_eliminated,
        maintenance_tasks=len(case.maintenance_mutations),
        median_latency_ns=latency,
        hard_gate_pass=hard_gate_pass,
        reasons=tuple(reasons),
    )


def decide_case(case: TournamentCase, results: Iterable[RepresentationResult]) -> TournamentDecision:
    case_results = [result for result in results if result.case_id == case.id]
    valid = [result for result in case_results if result.hard_gate_pass]
    if not valid:
        return TournamentDecision(case.id, None, (), "no competitor passed all hard gates")
    ordered = sorted(
        valid,
        key=lambda result: (
            -result.future_work_eliminated,
            result.adapter_failures,
            result.implementation_source_lines,
            result.serialized_bytes,
            result.execution_steps,
            result.competitor,
        ),
    )
    winner = ordered[0]
    return TournamentDecision(
        case.id,
        winner.competitor,
        tuple(result.competitor for result in ordered),
        "hard gates first; then future-work elimination, failures, implementation size, serialized size, execution steps",
    )


def load_corpus(path: str | Path) -> tuple[TournamentCase, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    cases: list[TournamentCase] = []
    for item in raw["cases"]:
        cases.append(
            TournamentCase(
                id=item["id"],
                domain=item["domain"],
                record=item["record"],
                required_keys=tuple(item["required_keys"]),
                evidence_keys=tuple(item.get("evidence_keys", ())),
                regeneration_required=bool(item.get("regeneration_required", False)),
                maintenance_mutations=tuple(item.get("maintenance_mutations", ())),
                no_abstraction_supported=bool(item.get("no_abstraction_supported", False)),
                adversarial_for_morph_genome=bool(item.get("adversarial_for_morph_genome", False)),
            )
        )
    return tuple(cases)


def run_tournament(path: str | Path) -> TournamentReport:
    path = Path(path)
    corpus_bytes = path.read_bytes()
    cases = load_corpus(path)
    results = tuple(evaluate_case(case, competitor) for case in cases for competitor in COMPETITORS)
    decisions = tuple(decide_case(case, results) for case in cases)

    morph_wins = sum(decision.winner == "MORPH_GENOME" for decision in decisions)
    adversarial_losses = all(
        decision.winner != "MORPH_GENOME"
        for case, decision in zip(cases, decisions)
        if case.adversarial_for_morph_genome
    )
    if morph_wins == len(decisions):
        disposition = "KEEP_BOUNDED"
        validity_domain = "only the frozen benchmark corpus; no universal optimality claim"
    elif morph_wins > 0:
        disposition = "NARROW"
        validity_domain = "retain MorphGenome only on frozen cases where it wins after hard gates and complexity charge"
    else:
        disposition = "PRUNE_GENERIC_CLAIM"
        validity_domain = "simpler representations dominate this frozen corpus; MorphGenome remains candidate-only outside it"
    if not adversarial_losses:
        disposition = "HOLD_FOR_FALSIFICATION"

    return TournamentReport(
        corpus_sha256=sha256(corpus_bytes).hexdigest(),
        results=results,
        decisions=decisions,
        morph_genome_disposition=disposition,
        validity_domain=validity_domain,
    )


def report_to_json(report: TournamentReport) -> str:
    payload = {
        "corpus_sha256": report.corpus_sha256,
        "stable_digest": report.stable_digest(),
        "results": [asdict(result) for result in report.results],
        "decisions": [asdict(decision) for decision in report.decisions],
        "morph_genome_disposition": report.morph_genome_disposition,
        "validity_domain": report.validity_domain,
        "global_pass": report.global_pass,
        "external_action_performed": report.external_action_performed,
        "auto_promoted": report.auto_promoted,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
