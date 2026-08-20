from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Iterable, Sequence

from .model import (
    IntentKind,
    IntentRelation,
    RelationHint,
    RelationKind,
    SourceAvailability,
    SourceEnvelope,
    StructuredIntent,
)


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _digest(parts: Iterable[str], prefix: str) -> str:
    payload = "\x1f".join(parts)
    return prefix + sha256(payload.encode("utf-8")).hexdigest()[:20]


def _intent_id(kind: IntentKind, text: str, source_id: str) -> str:
    return _digest((kind.value, _norm(text), source_id), "int_")


def _relation_id(kind: RelationKind, intent_ids: Sequence[str]) -> str:
    return _digest((kind.value, *sorted(intent_ids)), "rel_")


@dataclass(frozen=True)
class FederatedIntentReceipt:
    source_count: int
    present_source_count: int
    empty_source_count: int
    intent_count: int
    relation_count: int
    intents: tuple[StructuredIntent, ...]
    relations: tuple[IntentRelation, ...]
    source_ids: tuple[str, ...]
    oak_checks: tuple[str, ...]
    action_authorized: bool
    receipt_sha256: str

    def to_dict(self) -> dict:
        return {
            "source_count": self.source_count,
            "present_source_count": self.present_source_count,
            "empty_source_count": self.empty_source_count,
            "intent_count": self.intent_count,
            "relation_count": self.relation_count,
            "intents": [asdict(item) for item in self.intents],
            "relations": [asdict(item) for item in self.relations],
            "source_ids": list(self.source_ids),
            "oak_checks": list(self.oak_checks),
            "action_authorized": self.action_authorized,
            "receipt_sha256": self.receipt_sha256,
        }


class FederatedIntentCompiler:
    """Deterministic R0.1 compiler.

    The compiler performs only bounded transformations over caller-supplied source
    envelopes. It never executes a connector and never upgrades generated intent
    into authority.
    """

    def compile(
        self,
        sources: Iterable[SourceEnvelope],
        relation_hints: Iterable[RelationHint] = (),
    ) -> FederatedIntentReceipt:
        source_list = tuple(sorted(sources, key=lambda item: item.envelope_id))
        self._validate_unique_sources(source_list)

        intents: list[StructuredIntent] = []
        for source in source_list:
            intents.extend(self._compile_source(source))

        intents.sort(key=lambda item: item.intent_id)
        intent_by_id = {item.intent_id: item for item in intents}

        relations = self._duplicate_relations(intents)
        relations.extend(self._hint_relations(relation_hints, intent_by_id))
        relations = sorted({item.relation_id: item for item in relations}.values(), key=lambda item: item.relation_id)

        oak_checks = (
            "Source != Evidence",
            "Evidence != Intent",
            "Intent != Authority",
            "Authority != Action",
            "GeneratedIntent != AuthorizedIntent",
            "Empty source observation != negative domain claim",
        )

        payload = {
            "sources": [source.envelope_id for source in source_list],
            "intents": [
                {
                    "id": item.intent_id,
                    "kind": item.kind.value,
                    "text": item.text,
                    "sources": item.source_envelope_ids,
                    "evidence": item.evidence_refs,
                    "status": item.status,
                    "action_authorized": item.action_authorized,
                }
                for item in intents
            ],
            "relations": [
                {
                    "id": item.relation_id,
                    "kind": item.kind.value,
                    "intents": item.intent_ids,
                    "evidence": item.evidence_refs,
                    "inferred": item.inferred,
                }
                for item in relations
            ],
            "oak_checks": oak_checks,
            "action_authorized": False,
        }
        receipt_sha256 = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return FederatedIntentReceipt(
            source_count=len(source_list),
            present_source_count=sum(s.availability == SourceAvailability.PRESENT for s in source_list),
            empty_source_count=sum(s.availability == SourceAvailability.EMPTY for s in source_list),
            intent_count=len(intents),
            relation_count=len(relations),
            intents=tuple(intents),
            relations=tuple(relations),
            source_ids=tuple(source.envelope_id for source in source_list),
            oak_checks=oak_checks,
            action_authorized=False,
            receipt_sha256=receipt_sha256,
        )

    @staticmethod
    def _validate_unique_sources(sources: Sequence[SourceEnvelope]) -> None:
        keys = [(source.source_kind.value, source.source_id, source.fingerprint) for source in sources]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate source envelope")

    def _compile_source(self, source: SourceEnvelope) -> list[StructuredIntent]:
        intents: list[StructuredIntent] = []
        source_id = source.envelope_id
        evidence_refs = tuple(dict.fromkeys((*source.provenance, source.fingerprint)))

        for text in source.explicit_intents:
            intents.append(self._make_intent(IntentKind.EXPLICIT, text, source_id, evidence_refs))

        for claim in source.claims:
            intents.append(
                self._make_intent(
                    IntentKind.VERIFICATION,
                    f"Verify claim: {claim}",
                    source_id,
                    evidence_refs,
                )
            )
            intents.append(
                self._make_intent(
                    IntentKind.COUNTER,
                    f"Falsify claim: {claim}",
                    source_id,
                    evidence_refs,
                )
            )

        for residual in source.residuals:
            intents.append(
                self._make_intent(
                    IntentKind.RESIDUAL,
                    f"Resolve residual: {residual}",
                    source_id,
                    evidence_refs,
                )
            )

        for prohibition in source.prohibitions:
            intents.append(
                self._make_intent(IntentKind.NEGATIVE, prohibition, source_id, evidence_refs)
            )

        metadata = dict(source.metadata)
        if metadata.get("regenerable", "").lower() in {"1", "true", "yes"}:
            intents.append(
                self._make_intent(
                    IntentKind.REGENERATIVE,
                    "Regenerate this source projection from its canonical seed and re-verify the receipt",
                    source_id,
                    evidence_refs,
                )
            )

        # EMPTY is evidence about the observed connector result only. It must not
        # synthesize a claim that the domain itself contains nothing.
        if source.availability == SourceAvailability.EMPTY:
            intents.append(
                self._make_intent(
                    IntentKind.VERIFICATION,
                    "Re-observe source availability before relying on the empty snapshot",
                    source_id,
                    evidence_refs,
                )
            )

        return intents

    @staticmethod
    def _make_intent(
        kind: IntentKind,
        text: str,
        source_id: str,
        evidence_refs: tuple[str, ...],
    ) -> StructuredIntent:
        return StructuredIntent(
            intent_id=_intent_id(kind, text, source_id),
            kind=kind,
            text=" ".join(text.strip().split()),
            source_envelope_ids=(source_id,),
            evidence_refs=evidence_refs,
            status="PROPOSED",
            action_authorized=False,
        )

    @staticmethod
    def _duplicate_relations(intents: Sequence[StructuredIntent]) -> list[IntentRelation]:
        groups: dict[tuple[str, str], list[StructuredIntent]] = {}
        for intent in intents:
            key = (intent.kind.value, _norm(intent.text))
            groups.setdefault(key, []).append(intent)

        relations: list[IntentRelation] = []
        for group in groups.values():
            source_ids = {item.source_envelope_ids[0] for item in group}
            if len(group) < 2 or len(source_ids) < 2:
                continue
            intent_ids = tuple(sorted(item.intent_id for item in group))
            evidence = tuple(sorted({ref for item in group for ref in item.evidence_refs}))
            relations.append(
                IntentRelation(
                    relation_id=_relation_id(RelationKind.DUPLICATE, intent_ids),
                    kind=RelationKind.DUPLICATE,
                    intent_ids=intent_ids,
                    evidence_refs=evidence,
                    inferred=True,
                )
            )
        return relations

    @staticmethod
    def _hint_relations(
        hints: Iterable[RelationHint],
        intent_by_id: dict[str, StructuredIntent],
    ) -> list[IntentRelation]:
        relations: list[IntentRelation] = []
        for hint in hints:
            intent_ids = tuple(sorted(dict.fromkeys(hint.intent_ids)))
            if len(intent_ids) < 2:
                raise ValueError("relation hint requires at least two distinct intents")
            missing = [intent_id for intent_id in intent_ids if intent_id not in intent_by_id]
            if missing:
                raise ValueError(f"relation hint references unknown intents: {missing}")
            relations.append(
                IntentRelation(
                    relation_id=_relation_id(hint.kind, intent_ids),
                    kind=hint.kind,
                    intent_ids=intent_ids,
                    evidence_refs=hint.evidence_refs,
                    inferred=False,
                )
            )
        return relations

    @staticmethod
    def ucir_seed(receipt: FederatedIntentReceipt) -> dict:
        """Compact UCIR/BOOK0-compatible projection.

        This is an interoperability seed, not a claim that all external UCIR
        semantics are implemented here.
        """

        return {
            "mission_min": "Compile cross-source observations into proposed proof-carrying intents",
            "spec_min": {
                "source_count": receipt.source_count,
                "intent_count": receipt.intent_count,
                "relation_count": receipt.relation_count,
            },
            "evidence_min": list(receipt.source_ids),
            "tests_min": list(receipt.oak_checks),
            "authority": {
                "generated_intents_authorized": False,
                "external_action_authorized": False,
            },
            "receipt_sha256": receipt.receipt_sha256,
        }
