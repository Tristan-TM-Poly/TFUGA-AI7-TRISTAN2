from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from .adapters import adapt_capability, adapt_snapshot, component_manifest
from .core import Envelope, GraphEdge, InvariantCheck, ObjectRef, stable_digest
from .graphs import ResearchGraphKernel
from .ledger import ResearchTransitionLedger
from .receipts import issue_receipt, validate_receipt


class ResearchABICompiler:
    """Composition surface for the Universal Research ABI."""

    def __init__(self) -> None:
        self.kernel = ResearchGraphKernel()
        self.receipts: list[dict[str, Any]] = []
        self.transition_ledger = ResearchTransitionLedger()

    def ingest_capabilities(self, capabilities: Iterable[Any], *, provenance: tuple[str, ...] = ()) -> tuple[ObjectRef, ...]:
        return tuple(self.kernel.add(adapt_capability(cap, provenance=provenance)) for cap in capabilities)

    def ingest_snapshot(
        self,
        *,
        component: str,
        graph: str,
        object_type: str,
        object_id: str,
        payload: Mapping[str, Any],
        provenance: tuple[str, ...] = (),
        uncertainty: float = 0.0,
        oak_state: str = "UNKNOWN",
    ) -> ObjectRef:
        return self.kernel.add(adapt_snapshot(
            component=component,
            graph=graph,
            object_type=object_type,
            object_id=object_id,
            payload=payload,
            provenance=provenance,
            uncertainty=uncertainty,
            oak_state=oak_state,
        ))

    def add_object(self, envelope: Envelope) -> ObjectRef:
        return self.kernel.add(envelope)

    def link(
        self,
        source: ObjectRef,
        target: ObjectRef,
        relation: str,
        *,
        evidence_refs: Iterable[ObjectRef] = (),
        causal_claim: bool = False,
        uncertainty: float = 0.0,
    ) -> str:
        return self.kernel.link(GraphEdge(
            source=source,
            target=target,
            relation=relation,
            evidence_refs=tuple(evidence_refs),
            causal_claim=causal_claim,
            uncertainty=uncertainty,
        ))

    def transform(
        self,
        *,
        operator: str,
        inputs: Iterable[ObjectRef],
        outputs: Iterable[ObjectRef],
        assumptions: Iterable[str] = (),
        invariants: Iterable[InvariantCheck] = (),
        evidence_refs: Iterable[ObjectRef] = (),
        residuals: Iterable[str] = (),
        uncertainty: float = 0.0,
        cost: float = 0.0,
        authority: str = "read",
        risk: float = 0.0,
        rollback: str = "",
        provenance: Iterable[str] = (),
        oak_state: str = "UNKNOWN",
        state_before: str | None = None,
        state_after: str | None = None,
    ) -> dict[str, Any]:
        if (state_before is None) != (state_after is None):
            raise ValueError("state_before and state_after must be supplied together")
        receipt = issue_receipt(
            operator=operator,
            inputs=inputs,
            outputs=outputs,
            assumptions=assumptions,
            invariants=invariants,
            evidence_refs=evidence_refs,
            residuals=residuals,
            uncertainty=uncertainty,
            cost=cost,
            authority=authority,
            risk=risk,
            rollback=rollback,
            provenance=provenance,
            oak_state=oak_state,
        )
        validation = validate_receipt(receipt)
        record: dict[str, Any] = {"receipt": receipt.to_dict(), "validation": validation}
        if state_before is not None and state_after is not None:
            entry = self.transition_ledger.append(
                receipt,
                state_before=state_before,
                state_after=state_after,
            )
            record["ledger_entry"] = asdict(entry)
        self.receipts.append(record)
        return record

    def compile(self, *, max_per_graph: int = 8) -> dict[str, Any]:
        graph_validation = self.kernel.validate()
        packet = self.kernel.context_packet(max_per_graph=max_per_graph)
        payload = {
            "abi": "omega-universal-research-abi-r02",
            "graph_validation": graph_validation,
            "context": packet,
            "receipts": self.receipts,
            "transition_ledger": self.transition_ledger.to_dict(),
            "component_manifest": component_manifest(),
            "boundaries": [
                "claim != evidence",
                "capability != authority",
                "work != validation",
                "experiment != causal proof",
                "provenance != truth",
                "value != scientific validity",
                "similarity != semantic equivalence",
                "receipt != external truth certificate",
                "hash chain integrity != external signature or truth",
            ],
        }
        payload["fingerprint"] = stable_digest(payload)
        return payload
