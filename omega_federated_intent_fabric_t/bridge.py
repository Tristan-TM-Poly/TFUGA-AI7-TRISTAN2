from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from omega_intent_t.models import Intent

from .compiler import FederatedIntentReceipt


@dataclass(frozen=True)
class ExistingIntentBridgeReceipt:
    """Proof-carrying boundary to the existing Ω-INTENT-TO-EVERYTHING runtime."""

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


def to_existing_intent(receipt: FederatedIntentReceipt) -> Intent:
    """Compile a federated receipt into the repository's canonical `Intent` IR.

    This reuses `omega_intent_t.models.Intent` directly. The returned object is a
    planning input only; it does not call `IntentCompiler.compile`, materialize a
    WorkUnit, invoke a connector, or grant external authority.
    """

    seed = to_existing_intent_seed(receipt)
    expected_outputs = (
        "federated_source_manifest",
        "proof_carrying_intent_graph",
        "cross_source_relation_report",
        "oak_report",
    )
    completion_conditions = (
        "all_source_envelopes_have_provenance_or_fingerprint",
        "generated_intents_remain_proposed",
        "cross_source_relations_retain_evidence_refs",
        "no_external_action_is_authorized_by_generation",
        "oak_gate_passes",
    )
    return Intent.from_mapping(
        {
            "objective": seed.mission,
            "expected_outputs": expected_outputs,
            "epistemic_constraints": tuple(receipt.oak_checks),
            "completion_conditions": completion_conditions,
            "languages": ("python",),
            "mode": "focused",
            "metadata": {
                "federated_source_receipt_sha256": receipt.receipt_sha256,
                "source_count": receipt.source_count,
                "intent_count": receipt.intent_count,
                "relation_count": receipt.relation_count,
                "requirements": list(seed.requirements),
                "claims_to_verify": list(seed.claims_to_verify),
                "execution_authorized": False,
                "external_action_authorized": False,
            },
        }
    )


def to_capability_input(receipt: FederatedIntentReceipt) -> Mapping[str, Any]:
    """Minimal Capability OS handoff without invoking its runtime.

    Capability OS remains the authority-aware execution fabric below the existing
    intent layer. This function emits only the tokens a later separately authorized
    planner may consume.
    """

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
        "allow_mutation": False,
        "allow_irreversible": False,
    }
