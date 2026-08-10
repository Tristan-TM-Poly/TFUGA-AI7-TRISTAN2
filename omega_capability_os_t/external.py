from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .core import Capability, stable_digest
from .runtime import ActionRequired, HandlerResult

EXTERNAL_SCHEMA_VERSION = "0.3.0"
EXTERNAL_STATUSES = ("SUCCESS", "FAILURE", "DEGRADED")


def _template_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, str) and value.startswith("$") and len(value) > 1:
        tokens.add(value[1:])
    elif isinstance(value, Mapping):
        for item in value.values():
            tokens.update(_template_tokens(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            tokens.update(_template_tokens(item))
    return tokens


def _render_template(value: Any, inputs: Mapping[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$") and len(value) > 1:
        token = value[1:]
        if token not in inputs:
            raise KeyError(f"missing external adapter input token: {token}")
        return inputs[token]
    if isinstance(value, Mapping):
        return {str(key): _render_template(item, inputs) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_template(item, inputs) for item in value]
    if isinstance(value, tuple):
        return tuple(_render_template(item, inputs) for item in value)
    return value


@dataclass(frozen=True)
class ExternalBinding:
    capability_id: str
    connector: str
    action: str
    argument_template: Mapping[str, Any]
    adapter_version: str = EXTERNAL_SCHEMA_VERSION
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExternalBinding":
        template = payload.get("argument_template", {})
        if not isinstance(template, Mapping):
            raise TypeError("argument_template must be an object")
        return cls(
            capability_id=str(payload["capability_id"]),
            connector=str(payload["connector"]),
            action=str(payload["action"]),
            argument_template=dict(template),
            adapter_version=str(payload.get("adapter_version", EXTERNAL_SCHEMA_VERSION)),
            notes=tuple(map(str, payload.get("notes", []))),
        )

    @property
    def referenced_tokens(self) -> tuple[str, ...]:
        return tuple(sorted(_template_tokens(self.argument_template)))

    def render_arguments(self, inputs: Mapping[str, Any]) -> dict[str, Any]:
        rendered = _render_template(self.argument_template, inputs)
        if not isinstance(rendered, Mapping):
            raise TypeError("external adapter argument template must render to an object")
        return dict(rendered)


def load_external_bindings(payload: Mapping[str, Any]) -> tuple[ExternalBinding, ...]:
    return tuple(ExternalBinding.from_dict(item) for item in payload.get("bindings", []))


def validate_external_bindings(
    registry: Iterable[Capability],
    bindings: Iterable[ExternalBinding],
) -> dict[str, Any]:
    caps = {cap.capability_id: cap for cap in registry}
    items = tuple(bindings)
    errors: list[str] = []
    warnings: list[str] = []
    ids = [item.capability_id for item in items]
    duplicates = sorted({cid for cid in ids if ids.count(cid) > 1})
    if duplicates:
        errors.append(f"duplicate external bindings: {duplicates}")

    for binding in items:
        cap = caps.get(binding.capability_id)
        if cap is None:
            errors.append(f"{binding.capability_id}: binding targets unknown capability")
            continue
        if not binding.connector.strip() or not binding.action.strip():
            errors.append(f"{binding.capability_id}: connector/action cannot be empty")
        unknown_tokens = sorted(set(binding.referenced_tokens) - set(cap.consumes))
        if unknown_tokens:
            errors.append(
                f"{binding.capability_id}: argument template references undeclared inputs {unknown_tokens}"
            )
        unused_inputs = sorted(set(cap.consumes) - set(binding.referenced_tokens))
        if unused_inputs:
            warnings.append(
                f"{binding.capability_id}: capability inputs not represented in external arguments {unused_inputs}"
            )

    return {
        "schema": "omega-capability-external-binding-validation/v1",
        "status": "PASS" if not errors else "FAIL",
        "binding_count": len(items),
        "errors": errors,
        "warnings": warnings,
    }


@dataclass(frozen=True)
class ExternalActionRequest:
    request_id: str
    capability_id: str
    connector: str
    action: str
    authority: str
    arguments: Mapping[str, Any]
    expected_outputs: tuple[str, ...]
    candidate_sha: str | None = None
    plan_fingerprint: str | None = None

    def to_dict(self, *, include_arguments: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "omega-capability-external-request/v1",
            "request_id": self.request_id,
            "capability_id": self.capability_id,
            "connector": self.connector,
            "action": self.action,
            "authority": self.authority,
            "expected_outputs": list(self.expected_outputs),
            "candidate_sha": self.candidate_sha,
            "plan_fingerprint": self.plan_fingerprint,
            "arguments_fingerprint": stable_digest(dict(self.arguments)),
            "arguments_redacted": not include_arguments,
        }
        if include_arguments:
            payload["arguments"] = dict(self.arguments)
        return payload

    def execution_payload(self) -> dict[str, Any]:
        return self.to_dict(include_arguments=True)


@dataclass(frozen=True)
class ExternalActionReceipt:
    request_id: str
    capability_id: str
    connector: str
    action: str
    status: str
    outputs: Mapping[str, Any]
    sources: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    error: str | None = None
    observed_candidate_sha: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExternalActionReceipt":
        outputs = payload.get("outputs", {})
        if not isinstance(outputs, Mapping):
            raise TypeError("external receipt outputs must be an object")
        status = str(payload.get("status", "")).upper()
        if status not in EXTERNAL_STATUSES:
            raise ValueError(f"unknown external receipt status: {status}")
        return cls(
            request_id=str(payload["request_id"]),
            capability_id=str(payload["capability_id"]),
            connector=str(payload["connector"]),
            action=str(payload["action"]),
            status=status,
            outputs=dict(outputs),
            sources=tuple(map(str, payload.get("sources", []))),
            notes=tuple(map(str, payload.get("notes", []))),
            error=str(payload["error"]) if payload.get("error") is not None else None,
            observed_candidate_sha=(
                str(payload["observed_candidate_sha"])
                if payload.get("observed_candidate_sha") is not None
                else None
            ),
        )

    def to_dict(self, *, include_outputs: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "omega-capability-external-receipt/v1",
            "request_id": self.request_id,
            "capability_id": self.capability_id,
            "connector": self.connector,
            "action": self.action,
            "status": self.status,
            "sources": list(self.sources),
            "notes": list(self.notes),
            "error": self.error,
            "observed_candidate_sha": self.observed_candidate_sha,
            "outputs_fingerprint": stable_digest(dict(self.outputs)),
            "outputs_redacted": not include_outputs,
        }
        if include_outputs:
            payload["outputs"] = dict(self.outputs)
        return payload


def make_external_request(
    capability: Capability,
    binding: ExternalBinding,
    inputs: Mapping[str, Any],
    *,
    candidate_sha: str | None = None,
    plan_fingerprint: str | None = None,
) -> ExternalActionRequest:
    if binding.capability_id != capability.capability_id:
        raise ValueError("binding capability_id does not match capability")
    arguments = binding.render_arguments(inputs)
    identity = {
        "schema": EXTERNAL_SCHEMA_VERSION,
        "capability_id": capability.capability_id,
        "connector": binding.connector,
        "action": binding.action,
        "arguments_fingerprint": stable_digest(arguments),
        "candidate_sha": candidate_sha,
        "plan_fingerprint": plan_fingerprint,
    }
    request_id = f"EXT-{stable_digest(identity)[:24].upper()}"
    return ExternalActionRequest(
        request_id=request_id,
        capability_id=capability.capability_id,
        connector=binding.connector,
        action=binding.action,
        authority=capability.authority,
        arguments=arguments,
        expected_outputs=tuple(capability.produces),
        candidate_sha=candidate_sha,
        plan_fingerprint=plan_fingerprint,
    )


def validate_external_receipt(
    request: ExternalActionRequest,
    receipt: ExternalActionReceipt,
) -> dict[str, Any]:
    errors: list[str] = []
    if receipt.request_id != request.request_id:
        errors.append("request_id mismatch")
    if receipt.capability_id != request.capability_id:
        errors.append("capability_id mismatch")
    if receipt.connector != request.connector:
        errors.append("connector mismatch")
    if receipt.action != request.action:
        errors.append("action mismatch")
    if (
        request.candidate_sha
        and receipt.observed_candidate_sha
        and receipt.observed_candidate_sha != request.candidate_sha
    ):
        errors.append("observed_candidate_sha mismatch")
    missing_outputs = sorted(set(request.expected_outputs) - set(receipt.outputs))
    if receipt.status == "SUCCESS" and missing_outputs:
        errors.append(f"successful receipt missing declared outputs: {missing_outputs}")
    return {
        "schema": "omega-capability-external-receipt-validation/v1",
        "status": "PASS" if not errors else "FAIL",
        "receipt_status": receipt.status,
        "errors": errors,
        "missing_outputs": missing_outputs,
    }


class ExternalResolver:
    """Bridge between CapabilityRuntime and external ChatGPT/tool invocations.

    The resolver never invokes a connector itself. Missing receipts become a normalized,
    redacted ActionRequired request. A caller may execute that request through the real
    authorized connector, normalize the result into ExternalActionReceipt, then rerun the
    same plan with that receipt supplied.
    """

    def __init__(
        self,
        bindings: Iterable[ExternalBinding],
        *,
        receipts: Iterable[ExternalActionReceipt | Mapping[str, Any]] = (),
        candidate_sha: str | None = None,
        plan_fingerprint: str | None = None,
    ) -> None:
        self.bindings = {item.capability_id: item for item in bindings}
        parsed: list[ExternalActionReceipt] = []
        for item in receipts:
            parsed.append(item if isinstance(item, ExternalActionReceipt) else ExternalActionReceipt.from_dict(item))
        self.receipts = {item.request_id: item for item in parsed}
        self.candidate_sha = candidate_sha
        self.plan_fingerprint = plan_fingerprint
        self._pending: dict[str, ExternalActionRequest] = {}
        self._consumed: list[str] = []

    def __call__(self, capability: Capability, inputs: Mapping[str, Any]) -> HandlerResult:
        binding = self.bindings.get(capability.capability_id)
        if binding is None:
            raise LookupError(f"no external binding registered for {capability.capability_id}")
        request = make_external_request(
            capability,
            binding,
            inputs,
            candidate_sha=self.candidate_sha,
            plan_fingerprint=self.plan_fingerprint,
        )
        receipt = self.receipts.get(request.request_id)
        if receipt is None:
            self._pending[request.request_id] = request
            raise ActionRequired(
                f"external invocation required for {capability.capability_id}",
                action=request.to_dict(),
            )

        validation = validate_external_receipt(request, receipt)
        if validation["status"] != "PASS":
            raise RuntimeError("invalid external receipt: " + "; ".join(validation["errors"]))
        if receipt.status != "SUCCESS":
            detail = receipt.error or f"external receipt status={receipt.status}"
            raise RuntimeError(detail)

        self._consumed.append(receipt.request_id)
        return HandlerResult(
            outputs=dict(receipt.outputs),
            sources=tuple(receipt.sources),
            notes=(
                f"external_request_id={receipt.request_id}",
                f"external_connector={receipt.connector}",
                f"external_action={receipt.action}",
                *receipt.notes,
            ),
        )

    def pending_requests(self, *, include_arguments: bool = False) -> list[dict[str, Any]]:
        return [
            self._pending[key].to_dict(include_arguments=include_arguments)
            for key in sorted(self._pending)
        ]

    @property
    def consumed_receipt_ids(self) -> tuple[str, ...]:
        return tuple(self._consumed)
