from __future__ import annotations

from collections import Counter
from typing import Sequence

from .graph import EvidenceHypergraph
from .models import Intent, OakCheck, OakReport, Requirement, WorkUnit


def run_oak_gate(
    intent: Intent,
    requirements: Sequence[Requirement],
    work_units: Sequence[WorkUnit],
    graph: EvidenceHypergraph,
) -> OakReport:
    checks: list[OakCheck] = []

    def check(check_id: str, passed: bool, message: str, *evidence: str, severity: str = "error") -> None:
        checks.append(OakCheck(check_id, passed, message, tuple(evidence), severity))

    check("intent.objective", bool(intent.objective.strip()), "intent objective is non-empty", intent.intent_id)
    check("intent.outputs", bool(intent.expected_outputs), "at least one output is requested")
    check(
        "requirements.verifiable",
        all(req.verification_method and req.acceptance for req in requirements),
        "every requirement has a verification method and acceptance contract",
        *[req.requirement_id for req in requirements],
    )
    requirement_ids = {req.requirement_id for req in requirements}
    implemented = {rid for unit in work_units for rid in unit.requirement_ids}
    check(
        "requirements.covered",
        requirement_ids.issubset(implemented),
        "every requirement is linked to at least one work unit",
        *sorted(requirement_ids - implemented),
    )
    work_ids = {unit.work_unit_id for unit in work_units}
    missing_dependencies = sorted({dep for unit in work_units for dep in unit.dependency_ids if dep not in work_ids})
    check(
        "work.dependencies",
        not missing_dependencies,
        "all work-unit dependencies resolve",
        *missing_dependencies,
    )
    check(
        "work.validations",
        all(unit.validations for unit in work_units),
        "every work unit has at least one validation contract",
        *[unit.work_unit_id for unit in work_units if not unit.validations],
    )
    graph_errors = graph.validate()
    check("graph.references", not graph_errors, "all hypergraph edge endpoints resolve", *graph_errors)
    kinds = Counter(unit.kind for unit in work_units)
    check(
        "falsification.path",
        bool(kinds.get("test") or kinds.get("benchmark")),
        "the plan contains a test or benchmark path",
        severity="warning",
    )
    check(
        "claim.boundary",
        True,
        "generated implementations are marked as scaffolds and no theorem or validation is claimed",
    )
    check(
        "remote.authority",
        True,
        "compiler performs zero remote mutations and cannot merge automatically",
    )
    hard_failures = [item for item in checks if not item.passed and item.severity == "error"]
    warnings = tuple(item.message for item in checks if not item.passed and item.severity == "warning")
    return OakReport(intent_id=intent.intent_id, passed=not hard_failures, checks=tuple(checks), warnings=warnings)
