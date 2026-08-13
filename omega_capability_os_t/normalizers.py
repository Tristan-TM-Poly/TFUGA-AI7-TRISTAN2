from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .core import stable_digest
from .external import ExternalActionReceipt, ExternalActionRequest, validate_external_receipt

NORMALIZER_SCHEMA_VERSION = "0.5.0"
_PROVIDER_ALIASES = {
    "github": {"github"},
    "files": {"files", "library", "chatgptfiles"},
    "drive": {"drive", "googledrive"},
    "gmail": {"gmail"},
    "calendar": {"calendar", "googlecalendar"},
    "web": {"web", "webrun"},
}
_MISSING = object()


class ProviderResponseNormalizationError(ValueError):
    """Raised when a raw connector result cannot safely become a receipt."""


def _canon(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _selector_list(value: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _json_if_possible(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


def _unwrap_response(raw_response: Any) -> tuple[Any, Mapping[str, Any]]:
    """Return a useful body plus the original connector envelope when available."""
    raw_response = _json_if_possible(raw_response)
    envelope: Mapping[str, Any] = raw_response if isinstance(raw_response, Mapping) else {}
    body: Any = raw_response

    if isinstance(body, Mapping):
        result = body.get("result", _MISSING)
        if result is not _MISSING and result is not None:
            body = _json_if_possible(result)
        elif isinstance(body.get("structuredContent"), Mapping):
            body = body["structuredContent"]
        elif "content" in body:
            parsed = _json_if_possible(body["content"])
            if isinstance(parsed, (Mapping, list, tuple)):
                body = parsed

    if isinstance(body, Mapping):
        if isinstance(body.get("structuredContent"), Mapping):
            body = body["structuredContent"]
        elif "content" in body:
            parsed = _json_if_possible(body["content"])
            if isinstance(parsed, (Mapping, list, tuple)):
                body = parsed

    return body, envelope


def _path_get(root: Any, path: str) -> Any:
    if path in {"", "$", "."}:
        return root
    current = root
    normalized = path[2:] if path.startswith("$.") else path
    for part in normalized.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return _MISSING
            current = current[part]
            continue
        if isinstance(current, (list, tuple)):
            try:
                index = int(part)
            except ValueError:
                return _MISSING
            if index < 0 or index >= len(current):
                return _MISSING
            current = current[index]
            continue
        return _MISSING
    return current


def _select(root: Any, selectors: str | Sequence[str]) -> Any:
    for selector in _selector_list(selectors):
        value = _path_get(root, selector)
        if value is not _MISSING:
            return value
    return _MISSING


def _flatten_strings(value: Any) -> tuple[str, ...]:
    if value is _MISSING or value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(f"{key}={value[key]}" for key in sorted(value))
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _error_text(value: Any) -> str | None:
    if value in (None, False, "", {}, []):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("message", "detail", "error", "reason"):
            if value.get(key):
                return str(value[key])
        return json.dumps(dict(value), sort_keys=True, default=str)
    return str(value)


def _detect_error(envelope: Mapping[str, Any], body: Any) -> str | None:
    if envelope.get("is_error") is True:
        return _error_text(envelope.get("error")) or "connector reported is_error=true"
    error = _error_text(envelope.get("error"))
    if error:
        return error
    if isinstance(body, Mapping):
        if body.get("is_error") is True:
            return _error_text(body.get("error")) or "connector body reported is_error=true"
        body_error = _error_text(body.get("error"))
        if body_error:
            return body_error
    return None


def _verify_provider(request: ExternalActionRequest, provider: str) -> None:
    provider_key = _canon(provider)
    accepted = _PROVIDER_ALIASES.get(provider_key)
    if accepted is None:
        raise ProviderResponseNormalizationError(f"unknown provider normalizer: {provider}")
    connector = _canon(request.connector)
    if connector not in accepted:
        raise ProviderResponseNormalizationError(
            f"request connector {request.connector!r} is incompatible with {provider!r} normalizer"
        )


def _verify_envelope_identity(request: ExternalActionRequest, envelope: Mapping[str, Any]) -> None:
    connector_name = envelope.get("connector_name")
    if connector_name and _canon(str(connector_name)) != _canon(request.connector):
        raise ProviderResponseNormalizationError("raw response connector identity does not match request")
    action_name = envelope.get("action_name")
    if action_name and str(action_name) != request.action:
        raise ProviderResponseNormalizationError("raw response action identity does not match request")


@dataclass(frozen=True)
class ResponseContract:
    """Declarative mapping from one provider response to declared capability outputs."""

    provider: str
    output_paths: Mapping[str, str | Sequence[str]]
    candidate_sha_paths: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()
    mutation_ref_paths: tuple[str, ...] = ()
    require_candidate_sha: bool = True

    def validate_for(self, request: ExternalActionRequest) -> None:
        undeclared = sorted(set(self.output_paths) - set(request.expected_outputs))
        if undeclared:
            raise ProviderResponseNormalizationError(
                f"normalizer contract maps undeclared outputs: {undeclared}"
            )
        missing_contract = sorted(set(request.expected_outputs) - set(self.output_paths))
        if missing_contract:
            raise ProviderResponseNormalizationError(
                f"normalizer contract lacks declared outputs: {missing_contract}"
            )


def normalize_provider_response(
    request: ExternalActionRequest,
    raw_response: Any,
    contract: ResponseContract,
    *,
    observed_candidate_sha: str | None = None,
    mutation_performed: bool = False,
    mutation_refs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> ExternalActionReceipt:
    """Normalize a connector result without persisting its raw payload in the receipt."""

    _verify_provider(request, contract.provider)
    contract.validate_for(request)
    body, envelope = _unwrap_response(raw_response)
    _verify_envelope_identity(request, envelope)
    raw_fingerprint = stable_digest(raw_response)

    error = _detect_error(envelope, body)
    if error:
        receipt = ExternalActionReceipt(
            request_id=request.request_id,
            capability_id=request.capability_id,
            connector=request.connector,
            action=request.action,
            status="FAILURE",
            outputs={},
            notes=(
                f"normalizer_schema={NORMALIZER_SCHEMA_VERSION}",
                f"provider={contract.provider}",
                f"raw_response_fingerprint={raw_fingerprint}",
                *tuple(map(str, notes)),
            ),
            error=error,
            observed_candidate_sha=observed_candidate_sha,
            mutation_performed=mutation_performed,
            mutation_refs=tuple(map(str, mutation_refs)),
        )
        validation = validate_external_receipt(request, receipt)
        if validation["status"] != "PASS":
            raise ProviderResponseNormalizationError(
                "normalized connector failure violates receipt contract: "
                + "; ".join(validation["errors"])
            )
        return receipt

    outputs: dict[str, Any] = {}
    extraction_failures: list[str] = []
    for output_name in request.expected_outputs:
        value = _select(body, contract.output_paths[output_name])
        if value is _MISSING:
            extraction_failures.append(output_name)
        else:
            outputs[output_name] = value
    if extraction_failures:
        raise ProviderResponseNormalizationError(
            "successful raw response is missing declared outputs: "
            f"{sorted(extraction_failures)}"
        )

    candidate = observed_candidate_sha
    if candidate is None and contract.candidate_sha_paths:
        selected = _select(body, contract.candidate_sha_paths)
        if selected is not _MISSING and selected is not None:
            candidate = str(selected)
    if request.candidate_sha and contract.require_candidate_sha and not candidate:
        raise ProviderResponseNormalizationError(
            "candidate-SHA-bound request lacks an observed candidate SHA"
        )

    sources: list[str] = []
    for selector in contract.source_paths:
        sources.extend(_flatten_strings(_select(body, selector)))
    sources = list(dict.fromkeys(sources))

    extracted_mutation_refs: list[str] = list(map(str, mutation_refs))
    for selector in contract.mutation_ref_paths:
        extracted_mutation_refs.extend(_flatten_strings(_select(body, selector)))
    extracted_mutation_refs = list(dict.fromkeys(extracted_mutation_refs))

    receipt = ExternalActionReceipt(
        request_id=request.request_id,
        capability_id=request.capability_id,
        connector=request.connector,
        action=request.action,
        status="SUCCESS",
        outputs=outputs,
        sources=tuple(sources),
        notes=(
            f"normalizer_schema={NORMALIZER_SCHEMA_VERSION}",
            f"provider={contract.provider}",
            f"raw_response_fingerprint={raw_fingerprint}",
            *tuple(map(str, notes)),
        ),
        observed_candidate_sha=candidate,
        mutation_performed=mutation_performed,
        mutation_refs=tuple(extracted_mutation_refs),
    )
    validation = validate_external_receipt(request, receipt)
    if validation["status"] != "PASS":
        raise ProviderResponseNormalizationError(
            "normalized connector response violates receipt contract: "
            + "; ".join(validation["errors"])
        )
    return receipt


def _normalize(
    provider: str,
    request: ExternalActionRequest,
    raw_response: Any,
    *,
    output_paths: Mapping[str, str | Sequence[str]],
    candidate_sha_paths: Sequence[str] = (),
    source_paths: Sequence[str] = (),
    mutation_ref_paths: Sequence[str] = (),
    require_candidate_sha: bool = True,
    observed_candidate_sha: str | None = None,
    mutation_performed: bool = False,
    mutation_refs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> ExternalActionReceipt:
    return normalize_provider_response(
        request,
        raw_response,
        ResponseContract(
            provider=provider,
            output_paths=dict(output_paths),
            candidate_sha_paths=tuple(map(str, candidate_sha_paths)),
            source_paths=tuple(map(str, source_paths)),
            mutation_ref_paths=tuple(map(str, mutation_ref_paths)),
            require_candidate_sha=require_candidate_sha,
        ),
        observed_candidate_sha=observed_candidate_sha,
        mutation_performed=mutation_performed,
        mutation_refs=mutation_refs,
        notes=notes,
    )


def normalize_github_response(
    request: ExternalActionRequest,
    raw_response: Any,
    *,
    output_paths: Mapping[str, str | Sequence[str]],
    candidate_sha_paths: Sequence[str] = ("pull_request.head_sha", "head_sha", "commit.sha", "sha"),
    source_paths: Sequence[str] = ("url", "html_url", "display_url"),
    mutation_ref_paths: Sequence[str] = ("sha", "commit.sha", "url"),
    require_candidate_sha: bool = True,
    observed_candidate_sha: str | None = None,
    mutation_performed: bool = False,
    mutation_refs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> ExternalActionReceipt:
    return _normalize(
        "github", request, raw_response,
        output_paths=output_paths,
        candidate_sha_paths=candidate_sha_paths,
        source_paths=source_paths,
        mutation_ref_paths=mutation_ref_paths,
        require_candidate_sha=require_candidate_sha,
        observed_candidate_sha=observed_candidate_sha,
        mutation_performed=mutation_performed,
        mutation_refs=mutation_refs,
        notes=notes,
    )


def normalize_files_response(
    request: ExternalActionRequest,
    raw_response: Any,
    *,
    output_paths: Mapping[str, str | Sequence[str]],
    source_paths: Sequence[str] = ("url", "display_url", "resource_uri"),
    mutation_ref_paths: Sequence[str] = ("path", "uri", "resource_uri"),
    observed_candidate_sha: str | None = None,
    mutation_performed: bool = False,
    mutation_refs: Sequence[str] = (),
    notes: Sequence[str] = (),
) -> ExternalActionReceipt:
    return _normalize(
        "files", request, raw_response,
        output_paths=output_paths,
        source_paths=source_paths,
        mutation_ref_paths=mutation_ref_paths,
        require_candidate_sha=False,
        observed_candidate_sha=observed_candidate_sha,
        mutation_performed=mutation_performed,
        mutation_refs=mutation_refs,
        notes=notes,
    )


def normalize_drive_response(request: ExternalActionRequest, raw_response: Any, *, output_paths: Mapping[str, str | Sequence[str]], source_paths: Sequence[str] = ("url", "webViewLink", "display_url"), mutation_ref_paths: Sequence[str] = ("id", "file_id", "url"), observed_candidate_sha: str | None = None, mutation_performed: bool = False, mutation_refs: Sequence[str] = (), notes: Sequence[str] = ()) -> ExternalActionReceipt:
    return _normalize("drive", request, raw_response, output_paths=output_paths, source_paths=source_paths, mutation_ref_paths=mutation_ref_paths, require_candidate_sha=False, observed_candidate_sha=observed_candidate_sha, mutation_performed=mutation_performed, mutation_refs=mutation_refs, notes=notes)


def normalize_gmail_response(request: ExternalActionRequest, raw_response: Any, *, output_paths: Mapping[str, str | Sequence[str]], source_paths: Sequence[str] = ("permalink", "url"), mutation_ref_paths: Sequence[str] = ("id", "message_id", "thread_id"), observed_candidate_sha: str | None = None, mutation_performed: bool = False, mutation_refs: Sequence[str] = (), notes: Sequence[str] = ()) -> ExternalActionReceipt:
    return _normalize("gmail", request, raw_response, output_paths=output_paths, source_paths=source_paths, mutation_ref_paths=mutation_ref_paths, require_candidate_sha=False, observed_candidate_sha=observed_candidate_sha, mutation_performed=mutation_performed, mutation_refs=mutation_refs, notes=notes)


def normalize_calendar_response(request: ExternalActionRequest, raw_response: Any, *, output_paths: Mapping[str, str | Sequence[str]], source_paths: Sequence[str] = ("htmlLink", "url"), mutation_ref_paths: Sequence[str] = ("id", "event_id", "htmlLink"), observed_candidate_sha: str | None = None, mutation_performed: bool = False, mutation_refs: Sequence[str] = (), notes: Sequence[str] = ()) -> ExternalActionReceipt:
    return _normalize("calendar", request, raw_response, output_paths=output_paths, source_paths=source_paths, mutation_ref_paths=mutation_ref_paths, require_candidate_sha=False, observed_candidate_sha=observed_candidate_sha, mutation_performed=mutation_performed, mutation_refs=mutation_refs, notes=notes)


def normalize_web_response(request: ExternalActionRequest, raw_response: Any, *, output_paths: Mapping[str, str | Sequence[str]], source_paths: Sequence[str] = ("url", "display_url"), observed_candidate_sha: str | None = None, notes: Sequence[str] = ()) -> ExternalActionReceipt:
    return _normalize("web", request, raw_response, output_paths=output_paths, source_paths=source_paths, require_candidate_sha=False, observed_candidate_sha=observed_candidate_sha, mutation_performed=False, mutation_refs=(), notes=notes)
