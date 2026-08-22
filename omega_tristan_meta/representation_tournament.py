from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

COMPETITORS = ("morph_genome", "domain_specific", "minimal_dict", "no_abstraction")
EVIDENCE_CLASS = "SIMULATED_ENGINEERING"


@dataclass(frozen=True)
class FrozenTask:
    id: str
    domain: str
    source_ref: str
    required_fields: tuple[str, ...]
    payload: Mapping[str, Any]
    maintenance_family: str
    adversarial: bool = False


@dataclass(frozen=True)
class RepresentationResult:
    task_id: str
    domain: str
    competitor: str
    hard_gate_pass: bool
    frozen_probe_completion: float
    evidence_preservation: float
    provenance_preservation: float
    regeneration_closure: float
    mutation_detection: float
    persistent_complexity_bytes: int
    execution_cost_units: int
    translation_failure_rate: float
    future_work_eliminated: int
    evidence_class: str = EVIDENCE_CLASS


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _complexity_bytes(value: Any) -> int:
    return len(_canonical(value).encode("utf-8"))


def copy_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, sort_keys=True))


def _encode(task: FrozenTask, competitor: str) -> Any:
    payload = copy_payload(task.payload)
    if competitor == "morph_genome":
        return {
            "id": task.id,
            "purpose": payload.get("goal") or payload.get("need") or payload.get("prompt") or task.id,
            "state_schema": task.source_ref,
            "operators": sorted(payload),
            "constraints": payload.get("constraints", payload.get("risks", [])),
            "evidence_contracts": payload.get("evidence", []),
            "resources": [],
            "permissions": [],
            "memory_refs": [],
            "regeneration_rules": ["preserve_payload"],
            "parent_ids": [],
            "version": "0.2.0",
            "_payload": payload,
            "_source_ref": task.source_ref,
        }
    if competitor == "domain_specific":
        return {"type": task.source_ref, "payload": payload}
    if competitor == "minimal_dict":
        return {"src": task.source_ref, "p": payload}
    if competitor == "no_abstraction":
        return [task.source_ref, payload]
    raise ValueError(f"unknown competitor: {competitor}")


def _decode(representation: Any, competitor: str) -> tuple[str | None, dict[str, Any]]:
    if competitor == "morph_genome":
        return representation.get("_source_ref"), copy_payload(representation.get("_payload", {}))
    if competitor == "domain_specific":
        return representation.get("type"), copy_payload(representation.get("payload", {}))
    if competitor == "minimal_dict":
        return representation.get("src"), copy_payload(representation.get("p", {}))
    if competitor == "no_abstraction":
        if not isinstance(representation, list) or len(representation) != 2:
            return None, {}
        return representation[0], copy_payload(representation[1])
    raise ValueError(f"unknown competitor: {competitor}")


def _mutate_required_field(representation: Any, competitor: str, field: str) -> Any:
    mutated = json.loads(json.dumps(representation, sort_keys=True))
    if competitor == "morph_genome":
        mutated["_payload"].pop(field, None)
    elif competitor == "domain_specific":
        mutated["payload"].pop(field, None)
    elif competitor == "minimal_dict":
        mutated["p"].pop(field, None)
    elif competitor == "no_abstraction":
        mutated[1].pop(field, None)
    return mutated


def _execution_cost_units(competitor: str) -> int:
    return {"morph_genome": 5, "domain_specific": 3, "minimal_dict": 2, "no_abstraction": 1}[competitor]


def _future_work_eliminated(task: FrozenTask, competitor: str) -> int:
    if task.maintenance_family != "cross_domain":
        return 0
    return {"morph_genome": 2, "domain_specific": 0, "minimal_dict": 1, "no_abstraction": 0}[competitor]


def evaluate_representation(task: FrozenTask, competitor: str) -> RepresentationResult:
    representation = _encode(task, competitor)
    source_ref, decoded = _decode(representation, competitor)
    required = set(task.required_fields)
    completion = required <= set(decoded)
    evidence_preservation = decoded.get("evidence") == task.payload.get("evidence") if "evidence" in task.payload else True
    provenance_preservation = source_ref == task.source_ref
    regeneration = decoded == dict(task.payload)
    mutated = _mutate_required_field(representation, competitor, task.required_fields[0])
    _, mutated_payload = _decode(mutated, competitor)
    mutation_detection = task.required_fields[0] not in mutated_payload
    hard_gate_pass = all((completion, evidence_preservation, provenance_preservation, regeneration, mutation_detection))
    return RepresentationResult(
        task_id=task.id,
        domain=task.domain,
        competitor=competitor,
        hard_gate_pass=hard_gate_pass,
        frozen_probe_completion=float(completion),
        evidence_preservation=float(evidence_preservation),
        provenance_preservation=float(provenance_preservation),
        regeneration_closure=float(regeneration),
        mutation_detection=float(mutation_detection),
        persistent_complexity_bytes=_complexity_bytes(representation),
        execution_cost_units=_execution_cost_units(competitor),
        translation_failure_rate=0.0 if regeneration else 1.0,
        future_work_eliminated=_future_work_eliminated(task, competitor),
    )


def _dominates(a: RepresentationResult, b: RepresentationResult) -> bool:
    if not a.hard_gate_pass:
        return False
    if not b.hard_gate_pass:
        return True
    no_worse = (
        a.persistent_complexity_bytes <= b.persistent_complexity_bytes
        and a.execution_cost_units <= b.execution_cost_units
        and a.translation_failure_rate <= b.translation_failure_rate
        and a.future_work_eliminated >= b.future_work_eliminated
    )
    strictly_better = (
        a.persistent_complexity_bytes < b.persistent_complexity_bytes
        or a.execution_cost_units < b.execution_cost_units
        or a.translation_failure_rate < b.translation_failure_rate
        or a.future_work_eliminated > b.future_work_eliminated
    )
    return no_worse and strictly_better


def pareto_front(results: Sequence[RepresentationResult]) -> tuple[str, ...]:
    eligible = [result for result in results if result.hard_gate_pass]
    front = []
    for candidate in eligible:
        if not any(_dominates(other, candidate) for other in eligible if other != candidate):
            front.append(candidate.competitor)
    return tuple(sorted(front))


def load_corpus(path: str | Path) -> tuple[FrozenTask, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(
        FrozenTask(
            id=item["id"],
            domain=item["domain"],
            source_ref=item["source_ref"],
            required_fields=tuple(item["required_fields"]),
            payload=item["payload"],
            maintenance_family=item["maintenance_family"],
            adversarial=bool(item.get("adversarial", False)),
        )
        for item in raw["tasks"]
    )


def run_tournament(tasks: Iterable[FrozenTask]) -> dict[str, Any]:
    tasks = tuple(tasks)
    all_results: list[RepresentationResult] = []
    decisions = []
    morph_lost_adversarial = False
    for task in tasks:
        task_results = [evaluate_representation(task, competitor) for competitor in COMPETITORS]
        all_results.extend(task_results)
        front = pareto_front(task_results)
        morph_on_front = "morph_genome" in front
        if task.adversarial and not morph_on_front:
            morph_lost_adversarial = True
        decisions.append({
            "task_id": task.id,
            "domain": task.domain,
            "adversarial": task.adversarial,
            "pareto_front": list(front),
            "morph_genome_status": "BOUNDED_UTILITY" if morph_on_front else "PREFER_SIMPLER",
            "validity_domain": "cross-domain maintenance reuse with frozen probes" if morph_on_front else "direct/simple representation dominates on frozen probes",
        })

    m_plus, m_minus, m_query = [], [], []
    if any("morph_genome" in decision["pareto_front"] for decision in decisions):
        m_plus.append({
            "rule": "MorphGenome may remain Pareto-eligible when explicit cross-domain maintenance reuse offsets abstraction debt.",
            "evidence_class": EVIDENCE_CLASS,
        })
    if morph_lost_adversarial:
        m_minus.append({
            "rule": "Do not prefer MorphGenome for one-off tasks when a direct representation preserves all frozen probes at lower complexity/cost.",
            "evidence_class": EVIDENCE_CLASS,
        })
    if any(decision["morph_genome_status"] == "BOUNDED_UTILITY" for decision in decisions):
        m_query.append({
            "question": "Does the maintenance-reuse proxy predict real future-work reduction outside the frozen engineering corpus?",
            "evidence_class": EVIDENCE_CLASS,
        })

    core = {
        "version": "R0.2",
        "evidence_class": EVIDENCE_CLASS,
        "competitors": list(COMPETITORS),
        "task_count": len(tasks),
        "domains": sorted({task.domain for task in tasks}),
        "results": [asdict(result) for result in all_results],
        "decisions": decisions,
        "memory": {"M+": m_plus, "M-": m_minus, "M?": m_query},
        "hard_gates": [
            "Generated != Verified",
            "GenericRepresentation != BetterRepresentation",
            "Generator != Judge",
            "Capability != Authority",
            "Simulation != Reality",
            "LocalPASS != GlobalPASS",
        ],
        "scalar_score": "NOT_USED",
        "morph_lost_adversarial": morph_lost_adversarial,
    }
    digest = sha256(_canonical(core).encode("utf-8")).hexdigest()
    status = "PASS" if (
        len({task.domain for task in tasks}) >= 3
        and len(COMPETITORS) == 4
        and any(task.adversarial for task in tasks)
        and morph_lost_adversarial
        and all(result.hard_gate_pass for result in all_results)
    ) else "HOLD"
    return {**core, "status": status, "receipt_digest": digest}


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Frozen MorphGenome representation tournament R0.2")
    parser.add_argument("corpus")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    report = run_tournament(load_corpus(args.corpus))
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
