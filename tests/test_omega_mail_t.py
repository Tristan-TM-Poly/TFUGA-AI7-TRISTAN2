from __future__ import annotations

from copy import deepcopy

import pytest

from omega_mail_t.engine import ScenarioRunner
from omega_mail_t.models import MailMessage, Mailbox, deterministic_id
from omega_mail_t.oak import OAKDecision, OAKMailGate
from omega_mail_t.transport import DeliveryBlocked, InMemoryTransport


def make_transport() -> InMemoryTransport:
    transport = InMemoryTransport()
    transport.register(Mailbox("support@oak-systems.test", "oak", "support"))
    transport.register(Mailbox("research@research-foundry.test", "research", "research"))
    return transport


def test_internal_delivery_and_thread() -> None:
    transport = make_transport()
    message = MailMessage(
        message_id="mail_1",
        thread_id="thread_1",
        sender="research@research-foundry.test",
        recipients=("support@oak-systems.test",),
        subject="Test support",
        body="Synthetic request",
        intent="support_request",
        classification="support",
    )
    decision = transport.send(message)
    assert decision.decision == OAKDecision.ALLOW_SANDBOX
    assert transport.mailboxes["support@oak-systems.test"].latest() is message
    assert len(transport.mailboxes["support@oak-systems.test"].thread("thread_1")) == 1


def test_external_domain_is_blocked() -> None:
    transport = make_transport()
    message = MailMessage(
        message_id="mail_external",
        thread_id="thread_external",
        sender="research@research-foundry.test",
        recipients=("person@example.com",),
        subject="Blocked",
        body="Must never leave sandbox",
        intent="support_request",
    )
    with pytest.raises(DeliveryBlocked):
        transport.send(message)
    assert transport.events[-1].event == "DELIVERY_BLOCKED"


def test_deterministic_ids_are_reproducible() -> None:
    first = deterministic_id("scenario", 42, 0, "a@test.test")
    second = deterministic_id("scenario", 42, 0, "a@test.test")
    changed = deterministic_id("scenario", 43, 0, "a@test.test")
    assert first == second
    assert first != changed


def test_gate_blocks_non_synthetic_attachment_class() -> None:
    gate = OAKMailGate()
    message = MailMessage(
        message_id="mail_class",
        thread_id="thread_class",
        sender="research@research-foundry.test",
        recipients=("support@oak-systems.test",),
        subject="Classified",
        body="Synthetic",
        intent="research_review",
        data_classification="real_personal_data",
    )
    result = gate.evaluate(
        message,
        {"research@research-foundry.test", "support@oak-systems.test"},
    )
    assert result.decision == OAKDecision.BLOCK
    assert any(reason.startswith("disallowed_data_classification") for reason in result.reasons)


SCENARIO = {
    "scenario": {
        "id": "support_flow_001",
        "seed": 42017,
        "companies": [
            {
                "id": "research_foundry",
                "mailboxes": [
                    {"address": "research@research-foundry.test", "role": "research"}
                ],
            },
            {
                "id": "oak_systems",
                "mailboxes": [
                    {"address": "support@oak-systems.test", "role": "support"}
                ],
            },
        ],
        "participants": {
            "researcher": "research@research-foundry.test",
            "support": "support@oak-systems.test",
        },
        "steps": [
            {
                "action": "send",
                "from": "researcher",
                "to": "support",
                "intent": "support_request",
                "subject": "Validation du simulateur",
                "body": "Message synthétique.",
                "attachments": [{"filename": "trace.json", "media_type": "application/json"}],
            },
            {
                "action": "expect",
                "mailbox": "support",
                "assertions": [
                    {"type": "message_count", "equals": 1},
                    {"type": "latest_intent", "equals": "support_request"},
                    {"type": "latest_classification", "equals": "support"},
                    {"type": "latest_attachment_count", "equals": 1},
                ],
            },
        ],
    }
}


def test_scenario_runner_passes_and_is_deterministic() -> None:
    first = ScenarioRunner().run(deepcopy(SCENARIO))
    second = ScenarioRunner().run(deepcopy(SCENARIO))
    assert first["status"] == "PASS"
    assert first["assertion_count"] == 4
    first_id = first["transport"]["mailboxes"]["support@oak-systems.test"]["message_ids"][0]
    second_id = second["transport"]["mailboxes"]["support@oak-systems.test"]["message_ids"][0]
    assert first_id == second_id
