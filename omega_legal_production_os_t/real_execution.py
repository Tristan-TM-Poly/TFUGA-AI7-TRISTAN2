"""Execution and reconciliation orchestration for real provider adapters."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .http_client import HttpTransport
from .ledger import ActionLedger
from .models import ExternalActionEnvelope
from .real_providers import PROVIDERS, ProviderError, ProviderReceipt


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    action_id: str
    action_hash: str
    company_id: str
    provider_receipt: ProviderReceipt
    ledger_path: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": "omega-real-execution-receipt-v1",
            "action_id": self.action_id,
            "action_hash": self.action_hash,
            "company_id": self.company_id,
            "provider_receipt": self.provider_receipt.to_mapping(),
            "ledger_path": self.ledger_path,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ExecutionReceipt":
        provider = data["provider_receipt"]
        return cls(
            action_id=str(data["action_id"]),
            action_hash=str(data["action_hash"]),
            company_id=str(data["company_id"]),
            provider_receipt=ProviderReceipt(
                provider=str(provider["provider"]),
                operation=str(provider["operation"]),
                external_id=str(provider["external_id"]),
                status=str(provider["status"]),
                effect_confirmed=bool(provider["effect_confirmed"]),
                details=dict(provider.get("details", {})),
            ),
            ledger_path=str(data["ledger_path"]),
        )


def load_action(path: str | Path) -> ExternalActionEnvelope:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("action file must contain a JSON object")
    action = ExternalActionEnvelope.from_mapping(data)
    reasons = action.validate()
    if reasons:
        raise ValueError("invalid action: " + ",".join(reasons))
    supplied_hash = data.get("action_hash")
    if supplied_hash is not None and supplied_hash != action.action_hash:
        raise ValueError("action_hash in file does not match canonical content")
    return action


def _provider(name: str, transport: HttpTransport | None = None):
    provider_type = PROVIDERS.get(name)
    if provider_type is None:
        raise ValueError(f"unknown provider: {name}")
    return provider_type(transport=transport)


def execute_action(
    action_path: str | Path,
    *,
    provider_name: str,
    ledger_path: str | Path,
    receipt_path: str | Path,
    env: Mapping[str, str] | None = None,
    transport: HttpTransport | None = None,
) -> ExecutionReceipt:
    values = env or os.environ
    action = load_action(action_path)
    provider = _provider(provider_name, transport)
    ledger = ActionLedger(ledger_path)

    # Reservation is written before any provider call. A reserved hash cannot be
    # retried silently; a failed attempt requires explicit manual review and a
    # newly approved action envelope.
    ledger.reserve(action, provider=provider_name)
    ledger.append(action, event="EXECUTION_STARTED", provider=provider_name)
    try:
        provider_receipt = provider.execute(action, env=values)
    except Exception as exc:
        ledger.append(
            action,
            event="PROVIDER_REJECTED",
            provider=provider_name,
            provider_result={"error_type": type(exc).__name__, "message": str(exc)[:400]},
        )
        raise

    ledger.append(
        action,
        event="PROVIDER_ACCEPTED",
        provider=provider_name,
        provider_result=provider_receipt.to_mapping(),
    )
    if provider_receipt.effect_confirmed:
        ledger.append(
            action,
            event="EFFECT_CONFIRMED",
            provider=provider_name,
            provider_result=provider_receipt.to_mapping(),
        )
    receipt = ExecutionReceipt(
        action_id=action.action_id,
        action_hash=action.action_hash,
        company_id=action.company_id,
        provider_receipt=provider_receipt,
        ledger_path=str(Path(ledger_path)),
    )
    output = Path(receipt_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def reconcile_action(
    action_path: str | Path,
    receipt_path: str | Path,
    *,
    ledger_path: str | Path,
    output_path: str | Path,
    env: Mapping[str, str] | None = None,
    transport: HttpTransport | None = None,
) -> ExecutionReceipt:
    values = env or os.environ
    action = load_action(action_path)
    data = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("receipt file must contain a JSON object")
    receipt = ExecutionReceipt.from_mapping(data)
    if receipt.action_id != action.action_id or receipt.action_hash != action.action_hash:
        raise ProviderError("receipt is not bound to the exact action")
    provider = _provider(receipt.provider_receipt.provider, transport)
    reconciled = provider.reconcile(receipt.provider_receipt, env=values)
    ledger = ActionLedger(ledger_path)
    ledger.append(
        action,
        event="EFFECT_CONFIRMED" if reconciled.effect_confirmed else "EFFECT_UNKNOWN",
        provider=reconciled.provider,
        provider_result=reconciled.to_mapping(),
    )
    if reconciled.effect_confirmed:
        ledger.append(
            action,
            event="RECONCILED",
            provider=reconciled.provider,
            provider_result=reconciled.to_mapping(),
        )
    result = ExecutionReceipt(
        action_id=action.action_id,
        action_hash=action.action_hash,
        company_id=action.company_id,
        provider_receipt=reconciled,
        ledger_path=str(Path(ledger_path)),
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


PROVIDER_ENVIRONMENT = {
    "gmail-send": ("GMAIL_ACCESS_TOKEN", "OMEGA_RECIPIENT_EMAIL"),
    "github-release-draft": ("GITHUB_RELEASE_TOKEN",),
    "stripe-test-payment-intent": ("STRIPE_SECRET_KEY",),
    "dropbox-sign-test": ("DROPBOX_SIGN_API_KEY", "OMEGA_SIGNER_EMAIL"),
}


def doctor(provider_name: str, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    values = env or os.environ
    if provider_name not in PROVIDERS:
        raise ValueError(f"unknown provider: {provider_name}")
    required = (
        "OMEGA_EXTERNAL_EXECUTION_ACK",
        "OMEGA_ALLOWED_ACTION_ID",
        "OMEGA_ALLOWED_ACTION_HASH",
        "OMEGA_ALLOWED_PROVIDER",
        *PROVIDER_ENVIRONMENT[provider_name],
    )
    missing = [name for name in required if not values.get(name)]
    return {
        "provider": provider_name,
        "ready": not missing,
        "missing": missing,
        "secrets_printed": False,
    }
