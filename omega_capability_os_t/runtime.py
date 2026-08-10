from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .core import Capability, Intent, authority_allowed, effective_utility, health_status, outcome_record, plan, stable_digest


@dataclass(frozen=True)
class HandlerResult:
    outputs: Mapping[str, Any]
    sources: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @classmethod
    def coerce(cls, value: Any) -> "HandlerResult":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(outputs=dict(value))
        raise TypeError("capability handler must return a mapping or HandlerResult")


Handler = Callable[[Capability, Mapping[str, Any]], HandlerResult | Mapping[str, Any]]


def learn_health(records: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for record in records:
        cid = str(record["capability_id"])
        outcome = str(record["outcome"]).upper()
        bucket = buckets.setdefault(cid, {"SUCCESS": 0, "FAILURE": 0, "DEGRADED": 0})
        if outcome not in bucket:
            raise ValueError(f"unknown outcome: {outcome}")
        bucket[outcome] += 1

    snapshot: dict[str, dict[str, Any]] = {}
    for cid, counts in sorted(buckets.items()):
        if counts["FAILURE"] >= 2 and counts["SUCCESS"] == 0:
            status = "FAIL"
        elif counts["FAILURE"] or counts["DEGRADED"]:
            status = "DEGRADED"
        elif counts["SUCCESS"]:
            status = "PASS"
        else:
            status = "UNKNOWN"
        snapshot[cid] = {
            "status": status,
            "successes": counts["SUCCESS"],
            "failures": counts["FAILURE"],
            "degraded": counts["DEGRADED"],
            "m_plus": counts["SUCCESS"],
            "m_minus": counts["FAILURE"] + counts["DEGRADED"],
        }
    return snapshot


class CapabilityRuntime:
    def __init__(self, handlers: Mapping[str, Handler] | None = None) -> None:
        self.handlers: dict[str, Handler] = dict(handlers or {})

    def register(self, capability_id: str, handler: Handler) -> None:
        self.handlers[str(capability_id)] = handler

    def _invoke(
        self,
        cap: Capability,
        state: dict[str, Any],
    ) -> HandlerResult:
        handler = self.handlers.get(cap.capability_id)
        if handler is None:
            raise LookupError(f"no handler registered for {cap.capability_id}")
        inputs = {token: state[token] for token in cap.consumes if token in state}
        missing = [token for token in cap.consumes if token not in state]
        if missing:
            raise KeyError(f"missing runtime inputs for {cap.capability_id}: {missing}")
        result = HandlerResult.coerce(handler(cap, inputs))
        missing_outputs = [token for token in cap.produces if token not in result.outputs]
        if missing_outputs:
            raise ValueError(f"{cap.capability_id} omitted declared outputs: {missing_outputs}")
        return result

    def execute(
        self,
        registry: Iterable[Capability],
        intent: Intent,
        *,
        health: dict[str, Any] | None = None,
        initial_values: Mapping[str, Any] | None = None,
        candidate_sha: str | None = None,
        evidence_sha: str | None = None,
    ) -> dict[str, Any]:
        caps = tuple(registry)
        by_id = {cap.capability_id: cap for cap in caps}
        plan_payload = plan(caps, intent, health)
        state = dict(initial_values or {})
        for token in intent.available_inputs:
            state.setdefault(token, True)

        records: list[dict[str, Any]] = []
        observations: list[dict[str, Any]] = []
        sources: list[str] = []
        actions_required: list[dict[str, Any]] = []

        if plan_payload["status"] == "READY":
            for step in plan_payload["steps"]:
                cap = by_id[step["capability_id"]]
                attempted = [cap.capability_id]
                try:
                    result = self._invoke(cap, state)
                    state.update(result.outputs)
                    sources.extend(result.sources)
                    records.append(outcome_record(cap.capability_id, "SUCCESS"))
                    observations.append(
                        {
                            "capability_id": cap.capability_id,
                            "outcome": "SUCCESS",
                            "produced": list(cap.produces),
                            "output_hash": stable_digest({k: state[k] for k in cap.produces}),
                            "notes": list(result.notes),
                        }
                    )
                    continue
                except LookupError as exc:
                    actions_required.append(
                        {
                            "capability_id": cap.capability_id,
                            "reason": str(exc),
                            "consumes": list(cap.consumes),
                            "produces": list(cap.produces),
                            "authority": cap.authority,
                        }
                    )
                    observations.append(
                        {
                            "capability_id": cap.capability_id,
                            "outcome": "ACTION_REQUIRED",
                            "error": str(exc),
                        }
                    )
                    break
                except Exception as exc:
                    records.append(outcome_record(cap.capability_id, "FAILURE", symptom=str(exc)))
                    eligible_fallbacks = [
                        by_id[alt_id]
                        for alt_id in cap.alternatives
                        if alt_id in by_id
                        and authority_allowed(by_id[alt_id], intent)
                        and health_status(health, alt_id) != "FAIL"
                        and set(cap.produces).issubset(set(by_id[alt_id].produces))
                        and set(by_id[alt_id].consumes).issubset(set(state))
                    ]
                    eligible_fallbacks.sort(
                        key=lambda item: (effective_utility(item, health), item.capability_id),
                        reverse=True,
                    )
                    if not eligible_fallbacks:
                        observations.append(
                            {
                                "capability_id": cap.capability_id,
                                "outcome": "FAILURE",
                                "error": str(exc),
                            }
                        )
                        break
                    alt = eligible_fallbacks[0]
                    attempted.append(alt.capability_id)
                    try:
                        result = self._invoke(alt, state)
                        state.update(result.outputs)
                        sources.extend(result.sources)
                        records.append(
                            outcome_record(
                                alt.capability_id,
                                "SUCCESS",
                                recovery_chain=attempted,
                            )
                        )
                        observations.append(
                            {
                                "capability_id": cap.capability_id,
                                "outcome": "RECOVERED",
                                "error": str(exc),
                                "fallback": alt.capability_id,
                                "produced": list(alt.produces),
                            }
                        )
                        continue
                    except Exception as fallback_exc:
                        records.append(
                            outcome_record(
                                alt.capability_id,
                                "FAILURE",
                                symptom=str(fallback_exc),
                                recovery_chain=attempted,
                            )
                        )
                        observations.append(
                            {
                                "capability_id": cap.capability_id,
                                "outcome": "FAILURE",
                                "error": str(exc),
                                "fallback": alt.capability_id,
                                "fallback_error": str(fallback_exc),
                            }
                        )
                        break

        unresolved_runtime = [token for token in intent.required_outputs if token not in state]
        complete = plan_payload["status"] == "READY" and not unresolved_runtime and not actions_required
        fresh = bool(candidate_sha and evidence_sha and candidate_sha == evidence_sha)
        oak_status = "PASS" if complete and fresh else "HOLD"
        receipt = {
            "schema": "omega-capability-execution-receipt/v1",
            "intent_id": intent.intent_id,
            "plan_fingerprint": plan_payload.get("fingerprint"),
            "execution_status": "COMPLETE" if complete else "HOLD",
            "candidate_sha": candidate_sha,
            "evidence_sha": evidence_sha,
            "fresh": fresh,
            "required_outputs": list(intent.required_outputs),
            "unresolved_runtime_outputs": unresolved_runtime,
            "actions_required": actions_required,
            "observations": observations,
            "sources": sorted(set(sources)),
            "outcomes": records,
            "health_after": learn_health(records),
            "oak": {
                "status": oak_status,
                "boundary": (
                    "PASS certifies deterministic plan coverage, registered-handler completion, "
                    "declared outputs, and exact SHA freshness only."
                ),
            },
        }
        receipt["fingerprint"] = stable_digest(receipt)
        return receipt
