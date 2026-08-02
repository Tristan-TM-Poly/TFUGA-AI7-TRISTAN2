"""Duck-typed adapters to the existing Tristan ecosystem.

Adapters avoid hard dependencies so the package can be validated in isolation
while still accepting `omega_wiki_t.KnowledgeCell`-like objects and discovery
event records when those packages are available.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import (
    ActionProposal,
    ActionSensitivity,
    DiscoveryCell,
    Evidence,
    EvidenceKind,
    Hypothesis,
    MMinusRule,
    OakStatus,
)


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _status(value: Any) -> OakStatus:
    raw = getattr(value, "value", value)
    try:
        return OakStatus(str(raw))
    except ValueError:
        return OakStatus.IDEA


def knowledge_cell_to_discovery_cell(
    source: Any,
    *,
    user: str = "researcher",
    observable_pain: str = "knowledge is not executable or auditable",
    current_baseline: str = "manual document review",
) -> DiscoveryCell:
    title = str(_get(source, "title", _get(source, "name", "Imported knowledge cell")))
    domain = str(_get(source, "domain", "imported"))
    description = str(
        _get(source, "summary", _get(source, "description", "Imported structured claim set"))
    )
    source_claims = list(_get(source, "claims", ()))
    hypotheses: list[Hypothesis] = []
    for claim in source_claims:
        statement = str(_get(claim, "statement", _get(claim, "text", claim)))
        assumptions = tuple(str(item) for item in _get(claim, "assumptions", ("imported scope",)))
        falsification = tuple(
            str(item)
            for item in _get(
                claim,
                "falsification_conditions",
                _get(claim, "failure_conditions", ("requires explicit falsification condition",)),
            )
        )
        hypotheses.append(
            Hypothesis(
                statement=statement,
                domain=domain,
                assumptions=assumptions or ("imported scope",),
                falsification_conditions=falsification
                or ("requires explicit falsification condition",),
                value_potential=0.5,
                information_gain=0.5,
                falsifiability=0.5,
                reusability=0.5,
                cost=1.0,
                time_cost=1.0,
                operational_uncertainty=0.5,
                dependency_load=0.5,
                hypothesis_id=str(_get(claim, "claim_id", "")),
                status=_status(_get(claim, "status", OakStatus.IDEA)),
            )
        )
    if not hypotheses:
        hypotheses.append(
            Hypothesis(
                statement=description,
                domain=domain,
                assumptions=("imported source is represented faithfully",),
                falsification_conditions=("source-to-cell round trip fails",),
                value_potential=0.4,
                information_gain=0.4,
                falsifiability=0.5,
                reusability=0.5,
                cost=1.0,
                time_cost=1.0,
                operational_uncertainty=0.5,
                dependency_load=0.5,
            )
        )

    evidence: list[Evidence] = []
    source_evidence = list(_get(source, "evidence", ()))
    known_claim_ids = {h.hypothesis_id for h in hypotheses}
    for item in source_evidence:
        raw_kind = getattr(_get(item, "kind", "provenance"), "value", _get(item, "kind", "provenance"))
        try:
            kind = EvidenceKind(str(raw_kind))
        except ValueError:
            kind = EvidenceKind.PROVENANCE
        supports = tuple(
            identifier
            for identifier in (
                str(value) for value in _get(item, "supports", ())
            )
            if identifier in known_claim_ids
        )
        contradicts = tuple(
            identifier
            for identifier in (
                str(value) for value in _get(item, "contradicts", ())
            )
            if identifier in known_claim_ids
        )
        evidence.append(
            Evidence(
                kind=kind,
                title=str(_get(item, "title", "Imported evidence")),
                source=str(_get(item, "source", _get(item, "locator", "imported"))),
                supports=supports,
                contradicts=contradicts,
                independence=str(_get(item, "independence", "internal")),
                reproducibility=str(_get(item, "reproducibility", "unknown")),
                limitations=tuple(str(value) for value in _get(item, "limitations", ())),
                evidence_id=str(_get(item, "evidence_id", "")),
            )
        )

    imported_mminus: list[MMinusRule] = []
    for item in _get(source, "m_minus", _get(source, "negative_memory", ())):
        if isinstance(item, str):
            imported_mminus.append(
                MMinusRule(
                    trigger=item,
                    root_cause="Imported negative-memory statement",
                    forbidden_inference=item,
                    safe_replacement="Review source context before repeating the failed inference.",
                    prevention_test="source-linked review",
                    domain=domain,
                )
            )
        else:
            imported_mminus.append(
                MMinusRule(
                    trigger=str(_get(item, "trigger", "imported failure")),
                    root_cause=str(_get(item, "root_cause", "imported")),
                    forbidden_inference=str(
                        _get(item, "forbidden_inference", "do not repeat blindly")
                    ),
                    safe_replacement=str(
                        _get(item, "safe_replacement", "retest with explicit controls")
                    ),
                    prevention_test=str(
                        _get(item, "prevention_test", "source-linked regression")
                    ),
                    domain=str(_get(item, "domain", domain)),
                )
            )

    return DiscoveryCell(
        title=title,
        domain=domain,
        problem=description,
        user=user,
        observable_pain=observable_pain,
        current_baseline=current_baseline,
        hypotheses=hypotheses,
        evidence=evidence,
        m_minus=imported_mminus,
        code_refs=[str(value) for value in _get(source, "code_refs", ())],
        test_refs=[str(value) for value in _get(source, "test_refs", ())],
        next_actions=[
            ActionProposal(
                title="Audit imported discovery cell",
                rationale="Imported structure must be reviewed before OAK promotion.",
                sensitivity=ActionSensitivity.REVIEW_REQUIRED,
                reversible=True,
                expected_value=0.7,
                required_approvals=("domain-reviewer",),
            )
        ],
        status=_status(_get(source, "status", OakStatus.IDEA)),
        parent_ids=[str(_get(source, "cell_id", _get(source, "id", "imported")))],
    )


def event_records_to_mminus(records: Sequence[Any]) -> list[MMinusRule]:
    rules: list[MMinusRule] = []
    for record in records:
        event_type = str(_get(record, "event_type", _get(record, "type", "")))
        payload = _get(record, "payload", {})
        if event_type not in {"MMinusRule", "RefutationEvent", "FailureEvent"}:
            continue
        if not isinstance(payload, Mapping):
            payload = {}
        rules.append(
            MMinusRule(
                trigger=str(payload.get("trigger", event_type)),
                root_cause=str(payload.get("root_cause", "event-linked failure")),
                forbidden_inference=str(
                    payload.get("forbidden_inference", "do not repeat without redesign")
                ),
                safe_replacement=str(
                    payload.get("safe_replacement", "run a discriminating test")
                ),
                prevention_test=str(
                    payload.get("prevention_test", "event lineage regression")
                ),
                domain=str(payload.get("domain", "discovery-kernel")),
                source_event_ids=(str(_get(record, "event_id", "")),),
            )
        )
    return rules
