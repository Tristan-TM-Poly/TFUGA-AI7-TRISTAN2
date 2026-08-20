from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from typing import Iterable, Mapping, Sequence

from .compiler import FederatedIntentReceipt
from .model import IntentKind, IntentRelation, RelationKind, StructuredIntent


_MAX_EXACT_CANDIDATES = 18
_ACTIONABLE_RELATIONS = frozenset(
    {
        RelationKind.CONFLICT,
        RelationKind.PARTIAL,
        RelationKind.UNKNOWN,
        RelationKind.IMPLEMENTATION_GAP,
        RelationKind.DOCUMENTATION_GAP,
        RelationKind.EVIDENCE_GAP,
        RelationKind.REALITY_GAP,
        RelationKind.HARVEST_GAP,
    }
)
_REQUIRED_INTENT_KINDS = frozenset(
    {
        IntentKind.VERIFICATION,
        IntentKind.COUNTER,
        IntentKind.RESIDUAL,
    }
)


def _canon(value: str) -> str:
    return " ".join(value.strip().split())


def _digest(payload: Mapping[str, object], prefix: str) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return prefix + sha256(raw.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class EigenIntent:
    """Exact recurring intent invariant derived only from evidenced duplicates.

    R0.2 deliberately does not use fuzzy/embedding similarity to declare two intents
    equivalent. An EigenIntent is emitted only when the R0.1 relation layer already
    established an exact cross-source duplicate relation.
    """

    eigen_id: str
    family: str
    canonical_text: str
    member_intent_ids: tuple[str, ...]
    source_envelope_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    compression_gain: int
    action_authorized: bool = False

    def __post_init__(self) -> None:
        if len(self.member_intent_ids) < 2:
            raise ValueError("EigenIntent requires at least two member intents")
        if self.compression_gain != len(self.member_intent_ids) - 1:
            raise ValueError("compression_gain must equal members minus one")
        if self.action_authorized:
            raise ValueError("EigenIntent cannot authorize action")

    def to_dict(self) -> dict[str, object]:
        return {
            "eigen_id": self.eigen_id,
            "family": self.family,
            "canonical_text": self.canonical_text,
            "member_intent_ids": list(self.member_intent_ids),
            "source_envelope_ids": list(self.source_envelope_ids),
            "evidence_refs": list(self.evidence_refs),
            "compression_gain": self.compression_gain,
            "action_authorized": self.action_authorized,
        }


@dataclass(frozen=True)
class ClosureObligation:
    obligation_id: str
    kind: str
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "obligation_id": self.obligation_id,
            "kind": self.kind,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class MinimalUnlockSet:
    """Minimum/greedy set of proposed intents covering the current closure frontier.

    `exact_minimality_proven` is true only when exhaustive bounded enumeration was
    actually used. Large frontiers fall back to deterministic greedy set cover and
    therefore carry no minimum claim.
    """

    selected_intent_ids: tuple[str, ...]
    obligation_ids: tuple[str, ...]
    covered_obligation_ids: tuple[str, ...]
    uncovered_obligation_ids: tuple[str, ...]
    selection_method: str
    exact_minimality_proven: bool
    action_authorized: bool = False

    def __post_init__(self) -> None:
        if self.action_authorized:
            raise ValueError("MinimalUnlockSet cannot authorize action")
        if self.exact_minimality_proven and self.selection_method not in {
            "none",
            "exact_enumeration",
        }:
            raise ValueError("exact minimality requires exact enumeration or empty frontier")

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_intent_ids": list(self.selected_intent_ids),
            "obligation_ids": list(self.obligation_ids),
            "covered_obligation_ids": list(self.covered_obligation_ids),
            "uncovered_obligation_ids": list(self.uncovered_obligation_ids),
            "selection_method": self.selection_method,
            "exact_minimality_proven": self.exact_minimality_proven,
            "action_authorized": self.action_authorized,
        }


@dataclass(frozen=True)
class IntentClosureReceipt:
    source_receipt_sha256: str
    eigen_intents: tuple[EigenIntent, ...]
    derived_intents: tuple[StructuredIntent, ...]
    obligations: tuple[ClosureObligation, ...]
    unlock_set: MinimalUnlockSet
    oak_checks: tuple[str, ...]
    action_authorized: bool
    receipt_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_receipt_sha256": self.source_receipt_sha256,
            "eigen_intents": [item.to_dict() for item in self.eigen_intents],
            "derived_intents": [
                {
                    "intent_id": item.intent_id,
                    "kind": item.kind.value,
                    "text": item.text,
                    "source_envelope_ids": list(item.source_envelope_ids),
                    "evidence_refs": list(item.evidence_refs),
                    "status": item.status,
                    "action_authorized": item.action_authorized,
                }
                for item in self.derived_intents
            ],
            "obligations": [item.to_dict() for item in self.obligations],
            "unlock_set": self.unlock_set.to_dict(),
            "oak_checks": list(self.oak_checks),
            "action_authorized": self.action_authorized,
            "receipt_sha256": self.receipt_sha256,
        }


class IntentClosureCompiler:
    """Bounded R0.2 closure/compression pass over an R0.1 federated receipt."""

    def __init__(self, *, max_exact_candidates: int = _MAX_EXACT_CANDIDATES) -> None:
        if max_exact_candidates < 1:
            raise ValueError("max_exact_candidates must be >= 1")
        self.max_exact_candidates = max_exact_candidates

    def compile(self, receipt: FederatedIntentReceipt) -> IntentClosureReceipt:
        intent_by_id = {item.intent_id: item for item in receipt.intents}
        eigen_intents = self._derive_eigen_intents(receipt.relations, intent_by_id)
        derived_intents, relation_derived = self._derive_relation_intents(
            receipt.relations,
            intent_by_id,
        )
        obligations = self._derive_obligations(receipt.intents, receipt.relations)
        unlock_set = self._minimal_unlock_set(
            base_intents=receipt.intents,
            derived_intents=derived_intents,
            relations=receipt.relations,
            relation_derived=relation_derived,
            obligations=obligations,
        )

        oak_checks = (
            "Exact duplicate relation != semantic equivalence proof",
            "Eigen compression != permission to delete provenance",
            "Closure intent != execution authority",
            "MinimalUnlockSet != automatic execution plan",
            "Greedy cover != proven minimum",
            "Negative intent is a constraint, not an executable candidate",
        )

        payload = {
            "source_receipt_sha256": receipt.receipt_sha256,
            "eigen_intents": [item.to_dict() for item in eigen_intents],
            "derived_intents": [
                {
                    "intent_id": item.intent_id,
                    "kind": item.kind.value,
                    "text": item.text,
                    "source_envelope_ids": list(item.source_envelope_ids),
                    "evidence_refs": list(item.evidence_refs),
                }
                for item in derived_intents
            ],
            "obligations": [item.to_dict() for item in obligations],
            "unlock_set": unlock_set.to_dict(),
            "oak_checks": list(oak_checks),
            "action_authorized": False,
        }
        receipt_sha256 = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        return IntentClosureReceipt(
            source_receipt_sha256=receipt.receipt_sha256,
            eigen_intents=eigen_intents,
            derived_intents=derived_intents,
            obligations=obligations,
            unlock_set=unlock_set,
            oak_checks=oak_checks,
            action_authorized=False,
            receipt_sha256=receipt_sha256,
        )

    @staticmethod
    def _derive_eigen_intents(
        relations: Sequence[IntentRelation],
        intent_by_id: Mapping[str, StructuredIntent],
    ) -> tuple[EigenIntent, ...]:
        eigen: list[EigenIntent] = []
        for relation in relations:
            if relation.kind != RelationKind.DUPLICATE:
                continue
            members = tuple(intent_by_id[intent_id] for intent_id in relation.intent_ids)
            if len(members) < 2:
                continue
            family = members[0].kind.value
            canonical_text = _canon(members[0].text)
            if any(item.kind.value != family or _canon(item.text) != canonical_text for item in members[1:]):
                raise ValueError("duplicate relation members do not share exact intent semantics")
            source_ids = tuple(
                sorted({source_id for item in members for source_id in item.source_envelope_ids})
            )
            evidence = tuple(sorted({ref for item in members for ref in item.evidence_refs}))
            payload = {
                "family": family,
                "canonical_text": canonical_text,
                "member_intent_ids": list(sorted(relation.intent_ids)),
            }
            eigen.append(
                EigenIntent(
                    eigen_id=_digest(payload, "eigen_"),
                    family=family,
                    canonical_text=canonical_text,
                    member_intent_ids=tuple(sorted(relation.intent_ids)),
                    source_envelope_ids=source_ids,
                    evidence_refs=evidence,
                    compression_gain=len(members) - 1,
                    action_authorized=False,
                )
            )
        return tuple(sorted(eigen, key=lambda item: item.eigen_id))

    @staticmethod
    def _relation_text(relation: IntentRelation) -> str:
        prefix = {
            RelationKind.CONFLICT: "Resolve evidenced cross-source conflict",
            RelationKind.PARTIAL: "Acquire evidence to clarify partial correspondence",
            RelationKind.UNKNOWN: "Acquire discriminating evidence for unknown relation",
            RelationKind.IMPLEMENTATION_GAP: "Close evidenced implementation gap",
            RelationKind.DOCUMENTATION_GAP: "Close evidenced documentation gap",
            RelationKind.EVIDENCE_GAP: "Close evidenced evidence gap",
            RelationKind.REALITY_GAP: "Close evidenced reality gap",
            RelationKind.HARVEST_GAP: "Close evidenced harvest gap",
        }.get(relation.kind)
        if prefix is None:
            raise ValueError(f"relation kind is not actionable in R0.2: {relation.kind.value}")
        return f"{prefix}: {relation.relation_id}"

    def _derive_relation_intents(
        self,
        relations: Sequence[IntentRelation],
        intent_by_id: Mapping[str, StructuredIntent],
    ) -> tuple[tuple[StructuredIntent, ...], Mapping[str, str]]:
        derived: list[StructuredIntent] = []
        relation_derived: dict[str, str] = {}
        for relation in relations:
            if relation.kind not in _ACTIONABLE_RELATIONS:
                continue
            members = tuple(intent_by_id[intent_id] for intent_id in relation.intent_ids)
            source_ids = tuple(
                sorted({source_id for item in members for source_id in item.source_envelope_ids})
            )
            evidence = tuple(
                sorted({*relation.evidence_refs, *(ref for item in members for ref in item.evidence_refs)})
            )
            text = self._relation_text(relation)
            intent_id = _digest(
                {
                    "kind": IntentKind.DERIVED.value,
                    "relation_id": relation.relation_id,
                    "text": text,
                },
                "int_",
            )
            item = StructuredIntent(
                intent_id=intent_id,
                kind=IntentKind.DERIVED,
                text=text,
                source_envelope_ids=source_ids,
                evidence_refs=evidence,
                status="PROPOSED",
                action_authorized=False,
            )
            derived.append(item)
            relation_derived[relation.relation_id] = intent_id
        return tuple(sorted(derived, key=lambda item: item.intent_id)), relation_derived

    @staticmethod
    def _derive_obligations(
        intents: Sequence[StructuredIntent],
        relations: Sequence[IntentRelation],
    ) -> tuple[ClosureObligation, ...]:
        obligations: list[ClosureObligation] = []
        for intent in intents:
            if intent.kind not in _REQUIRED_INTENT_KINDS:
                continue
            obligations.append(
                ClosureObligation(
                    obligation_id=f"intent:{intent.intent_id}",
                    kind=intent.kind.value,
                    evidence_refs=tuple(sorted(intent.evidence_refs)),
                )
            )
        for relation in relations:
            if relation.kind not in _ACTIONABLE_RELATIONS:
                continue
            obligations.append(
                ClosureObligation(
                    obligation_id=f"relation:{relation.relation_id}",
                    kind=relation.kind.value,
                    evidence_refs=tuple(sorted(relation.evidence_refs)),
                )
            )
        return tuple(sorted(obligations, key=lambda item: item.obligation_id))

    def _minimal_unlock_set(
        self,
        *,
        base_intents: Sequence[StructuredIntent],
        derived_intents: Sequence[StructuredIntent],
        relations: Sequence[IntentRelation],
        relation_derived: Mapping[str, str],
        obligations: Sequence[ClosureObligation],
    ) -> MinimalUnlockSet:
        obligation_ids = tuple(item.obligation_id for item in obligations)
        if not obligation_ids:
            return MinimalUnlockSet(
                selected_intent_ids=(),
                obligation_ids=(),
                covered_obligation_ids=(),
                uncovered_obligation_ids=(),
                selection_method="none",
                exact_minimality_proven=True,
                action_authorized=False,
            )

        all_intents = tuple(base_intents) + tuple(derived_intents)
        coverage: dict[str, set[str]] = {item.intent_id: set() for item in all_intents}

        for intent in base_intents:
            own_obligation = f"intent:{intent.intent_id}"
            if intent.kind in _REQUIRED_INTENT_KINDS:
                coverage[intent.intent_id].add(own_obligation)

        for relation in relations:
            if relation.kind not in _ACTIONABLE_RELATIONS:
                continue
            obligation_id = f"relation:{relation.relation_id}"
            for intent_id in relation.intent_ids:
                coverage.setdefault(intent_id, set()).add(obligation_id)
            derived_id = relation_derived.get(relation.relation_id)
            if derived_id:
                coverage.setdefault(derived_id, set()).add(obligation_id)

        # Negative intents constrain admissibility but are never scheduled as actions.
        negative_ids = {item.intent_id for item in base_intents if item.kind == IntentKind.NEGATIVE}
        candidate_ids = tuple(
            sorted(
                intent_id
                for intent_id, covered in coverage.items()
                if covered and intent_id not in negative_ids
            )
        )
        universe = set(obligation_ids)

        selected: tuple[str, ...]
        method: str
        exact = False
        if len(candidate_ids) <= self.max_exact_candidates:
            selected = self._exact_cover(candidate_ids, coverage, universe)
            method = "exact_enumeration"
            exact = bool(selected) or not universe
        else:
            selected = self._greedy_cover(candidate_ids, coverage, universe)
            method = "deterministic_greedy"

        covered = set().union(*(coverage[item_id] for item_id in selected)) if selected else set()
        uncovered = universe - covered
        if uncovered:
            exact = False

        return MinimalUnlockSet(
            selected_intent_ids=selected,
            obligation_ids=tuple(sorted(universe)),
            covered_obligation_ids=tuple(sorted(covered)),
            uncovered_obligation_ids=tuple(sorted(uncovered)),
            selection_method=method,
            exact_minimality_proven=exact,
            action_authorized=False,
        )

    @staticmethod
    def _exact_cover(
        candidate_ids: Sequence[str],
        coverage: Mapping[str, set[str]],
        universe: set[str],
    ) -> tuple[str, ...]:
        for size in range(1, len(candidate_ids) + 1):
            for combo in combinations(candidate_ids, size):
                covered = set().union(*(coverage[item_id] for item_id in combo))
                if universe.issubset(covered):
                    return tuple(combo)
        return ()

    @staticmethod
    def _greedy_cover(
        candidate_ids: Sequence[str],
        coverage: Mapping[str, set[str]],
        universe: set[str],
    ) -> tuple[str, ...]:
        remaining = set(universe)
        selected: list[str] = []
        available = set(candidate_ids)
        while remaining:
            ranked = sorted(
                (
                    (-len(coverage[item_id] & remaining), item_id)
                    for item_id in available
                    if coverage[item_id] & remaining
                )
            )
            if not ranked:
                break
            _, winner = ranked[0]
            selected.append(winner)
            remaining -= coverage[winner]
            available.remove(winner)
        return tuple(selected)

    @staticmethod
    def next_intent_seed(receipt: IntentClosureReceipt) -> dict[str, object]:
        """BOOK0-min projection for a separately authorized next compilation pass."""

        return {
            "mission_min": "Close the current evidenced intent frontier with minimum persistent work",
            "source_receipt_sha256": receipt.source_receipt_sha256,
            "closure_receipt_sha256": receipt.receipt_sha256,
            "selected_proposed_intent_ids": list(receipt.unlock_set.selected_intent_ids),
            "uncovered_obligation_ids": list(receipt.unlock_set.uncovered_obligation_ids),
            "selection_method": receipt.unlock_set.selection_method,
            "exact_minimality_proven": receipt.unlock_set.exact_minimality_proven,
            "authority": {
                "execution_authorized": False,
                "merge_authorized": False,
                "publish_authorized": False,
            },
        }
