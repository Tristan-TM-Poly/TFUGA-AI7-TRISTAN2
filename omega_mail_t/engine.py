"""Scenario compiler and assertion engine for Ω-MAIL-T."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import Attachment, MailMessage, Mailbox, deterministic_id, recipients_tuple
from .transport import DeliveryBlocked, InMemoryTransport


CLASSIFICATION_BY_INTENT = {
    "support_request": "support",
    "invoice_dispute": "billing_dispute",
    "security_alert": "security",
    "research_review": "research",
    "publication_approval": "ip_approval",
    "software_patch": "engineering",
}


@dataclass(frozen=True, slots=True)
class AssertionResult:
    passed: bool
    assertion_type: str
    expected: Any
    observed: Any
    message: str


class ScenarioRunner:
    def __init__(self, transport: InMemoryTransport | None = None) -> None:
        self.transport = transport or InMemoryTransport()
        self.sent: list[MailMessage] = []
        self.assertions: list[AssertionResult] = []
        self.failures: list[dict[str, Any]] = []

    @staticmethod
    def load(path: str | Path) -> dict[str, Any]:
        """Load the dependency-free JSON subset of YAML.

        JSON is valid YAML, so ``*.yaml`` fixtures can remain YAML-compatible
        without adding a runtime parser dependency to the repository.
        """
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def run(self, document: dict[str, Any]) -> dict[str, Any]:
        scenario = document.get("scenario", document)
        scenario_id = str(scenario["id"])
        seed = int(scenario.get("seed", 0))
        self._register_companies(scenario.get("companies", []))

        aliases = {
            str(alias): str(address).lower()
            for alias, address in scenario.get("participants", {}).items()
        }

        for index, step in enumerate(scenario.get("steps", [])):
            action = step.get("action")
            if action == "send":
                self._send_step(scenario_id, seed, index, step, aliases)
            elif action == "expect":
                self._expect_step(step, aliases)
            else:
                raise ValueError(f"Unsupported scenario action: {action!r}")

        passed = all(result.passed for result in self.assertions) and not self.failures
        return {
            "scenario_id": scenario_id,
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "message_count": len(self.sent),
            "assertion_count": len(self.assertions),
            "assertions": [asdict(result) for result in self.assertions],
            "failures": self.failures,
            "transport": self.transport.snapshot(),
        }

    def _register_companies(self, companies: list[dict[str, Any]]) -> None:
        for company in companies:
            company_id = str(company["id"])
            for mailbox in company.get("mailboxes", []):
                self.transport.register(
                    Mailbox(
                        address=str(mailbox["address"]),
                        company_id=company_id,
                        role=str(mailbox.get("role", "unspecified")),
                        languages=tuple(mailbox.get("languages", ["fr-CA"])),
                    )
                )

    def _resolve(self, value: str, aliases: dict[str, str]) -> str:
        return aliases.get(value, value).lower()

    def _send_step(
        self,
        scenario_id: str,
        seed: int,
        index: int,
        step: dict[str, Any],
        aliases: dict[str, str],
    ) -> None:
        sender = self._resolve(str(step["from"]), aliases)
        recipient_values = step["to"] if isinstance(step["to"], list) else [step["to"]]
        recipients = tuple(self._resolve(str(value), aliases) for value in recipient_values)
        intent = str(step.get("intent", "unspecified"))
        message_id = deterministic_id(scenario_id, seed, index, sender, recipients, intent)
        reply_to = step.get("reply_to")
        if reply_to is not None:
            parent = self.sent[int(reply_to)]
            thread_id = parent.thread_id
        else:
            thread_id = deterministic_id(scenario_id, seed, step.get("thread", index), prefix="thread")

        attachments = tuple(
            Attachment(
                filename=str(raw["filename"]),
                media_type=str(raw.get("media_type", "application/octet-stream")),
                content_sha256=str(raw.get("content_sha256", "synthetic")),
                size_bytes=int(raw.get("size_bytes", 0)),
                synthetic=bool(raw.get("synthetic", True)),
            )
            for raw in step.get("attachments", [])
        )

        message = MailMessage(
            message_id=message_id,
            thread_id=thread_id,
            sender=sender,
            recipients=recipients_tuple(recipients),
            subject=str(step.get("subject", intent.replace("_", " ").title())),
            body=str(step.get("body", "Synthetic scenario message.")),
            intent=intent,
            language=str(step.get("language", "fr-CA")),
            classification=str(step.get("classification", CLASSIFICATION_BY_INTENT.get(intent, "unclassified"))),
            data_classification=str(step.get("data_classification", "synthetic_internal")),
            attachments=attachments,
            metadata=dict(step.get("metadata", {})),
        )

        try:
            self.transport.send(message)
            self.sent.append(message)
        except DeliveryBlocked as exc:
            self.failures.append(
                {
                    "step": index,
                    "type": "DELIVERY_BLOCKED",
                    "message_id": message_id,
                    "reason": str(exc),
                }
            )

    def _expect_step(self, step: dict[str, Any], aliases: dict[str, str]) -> None:
        mailbox_address = self._resolve(str(step["mailbox"]), aliases)
        mailbox = self.transport.mailboxes.get(mailbox_address)
        for assertion in step.get("assertions", []):
            assertion_type = str(assertion["type"])
            expected = assertion.get("equals", assertion.get("value", True))
            observed: Any

            if mailbox is None:
                observed = None
            elif assertion_type == "message_count":
                observed = len(mailbox.messages)
            elif assertion_type == "latest_intent":
                latest = mailbox.latest()
                observed = latest.intent if latest else None
            elif assertion_type == "latest_classification":
                latest = mailbox.latest()
                observed = latest.classification if latest else None
            elif assertion_type == "latest_language":
                latest = mailbox.latest()
                observed = latest.language if latest else None
            elif assertion_type == "latest_attachment_count":
                latest = mailbox.latest()
                observed = len(latest.attachments) if latest else None
            elif assertion_type == "thread_message_count":
                latest = mailbox.latest()
                observed = len(mailbox.thread(latest.thread_id)) if latest else 0
            else:
                raise ValueError(f"Unsupported assertion type: {assertion_type!r}")

            passed = observed == expected
            self.assertions.append(
                AssertionResult(
                    passed=passed,
                    assertion_type=assertion_type,
                    expected=expected,
                    observed=observed,
                    message="ok" if passed else f"Expected {expected!r}, observed {observed!r}",
                )
            )


def run_scenario(path: str | Path) -> dict[str, Any]:
    runner = ScenarioRunner()
    return runner.run(runner.load(path))
