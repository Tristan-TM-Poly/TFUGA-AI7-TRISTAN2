from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .compiler import FederatedIntentReceipt


@dataclass(frozen=True)
class ExistingIntentBridgeReceipt:
    """Proof-carrying boundary to an existing intent/capability runtime.

    R0.1 deliberately exchanges only plain data. It does not import a second
    planner, execute a WorkUnit, or infer connector authority.
    """

    mission: str
    requirements: tuple[str, ...]
    claims_to_verify: tuple[str, ...]
    source_receipt_sha256: str
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized:
            raise ValueError("federated bridge cannot authorize execution")


def to_existing_intent_seed(receipt: FederatedIntentReceipt) -> ExistingIntentBridgeReceipt:
    requirements = tuple(
        sorted(
            {
                intent.text
                for intent in receipt.intents
                if intent.kind.value in {"explicit", "residual", "regenerative"}
            }
        )
    )
    claims = tuple(
        sorted(
            {
                intent.text.removeprefix("Verify claim: ")
                for intent in receipt.intents
                if intent.kind.value == "verification" and intent.text.startswith("Verify claim: ")
            }
        )
    )
    return ExistingIntentBridgeReceipt(
        mission="Compile federated source observations through the existing intent runtime",
        requirements=requirements,
        claims_to_verify=claims,
        source_receipt_sha256=receipt.receipt_sha256,
        execution_authorized=False,
    )


def to_capability_input(receipt: FederatedIntentReceipt) -> Mapping[str, Any]:
    """Minimal capability-planner handoff without importing or executing it."""

    return {
        "required_capabilities": sorted(
            {
                "verify",
                "falsify",
                "provenance",
                "cross_source_compare" if receipt.source_count > 1 else "single_source_verify",
            }
        ),
        "source_receipt_sha256": receipt.receipt_sha256,
        "intent_count": receipt.intent_count,
        "relation_count": receipt.relation_count,
        "execution_authorized": False,
    }
