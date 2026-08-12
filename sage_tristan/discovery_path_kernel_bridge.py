"""Bridge Ω-DISCOVERY-PATH R0.4 into the existing discovery event envelope.

The bridge records a path model as workflow events.  It does not assert that
those workflow events are the historical causal sequence that produced the
discovery.  The existing Ω-DISCOVERY-KERNEL remains the event/evidence ledger;
DiscoveryPath remains the trajectory/program IR.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from omega_discovery_kernel_t.events import DiscoveryEvent
from sage_tristan.discovery_path_ir import DiscoveryPath


@dataclass(frozen=True, slots=True)
class BridgeReceipt:
    path_id: str
    event_ids: tuple[str, ...]
    event_types: tuple[str, ...]
    parentage_valid: bool
    contracts_valid: bool
    validation_issues: tuple[str, ...]
    historical_causation_certified: bool = False


def _timestamp_series(count: int) -> tuple[str, ...]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        (start + timedelta(seconds=index)).isoformat().replace("+00:00", "Z")
        for index in range(count)
    )


def path_to_kernel_events(path: DiscoveryPath) -> tuple[DiscoveryEvent, ...]:
    """Encode a DiscoveryPath as a reversible workflow-record event chain."""
    timestamps = iter(_timestamp_series(len(path.steps) + 5))
    subject_id = f"discovery-path::{path.path_id}"

    observation = DiscoveryEvent.create(
        "ObservationEvent",
        subject_id,
        next(timestamps),
        provenance=path.source_ids,
        status="candidate",
        payload={
            "observation_kind": "discovery_path_model",
            "path_id": path.path_id,
            "initial_state_id": path.initial_state.state_id,
            "initial_year": path.initial_state.year,
        },
    )
    claim = DiscoveryEvent.create(
        "ClaimEvent",
        subject_id,
        next(timestamps),
        parent_ids=(observation.event_id,),
        provenance=path.source_ids,
        status="candidate",
        payload={
            "claim_id": path.target_discovery_id,
            "text": "A candidate path model reaches the encoded target under declared operators and gates.",
            "failure_conditions": [
                "path audit fails",
                "evidence leakage is detected",
                "operator contract is invalid",
                "terminal state does not contain target",
            ],
            "claim_class": path.claim_class.value,
            "historical_causation_claim": False,
        },
    )

    events: list[DiscoveryEvent] = [observation, claim]
    parent = claim
    for step in path.steps:
        event = DiscoveryEvent.create(
            "GeneratorCandidate",
            subject_id,
            next(timestamps),
            parent_ids=(parent.event_id,),
            provenance=path.source_ids,
            status="candidate",
            payload={
                "continuous_generators": [],
                "discrete_events": [step.operator_id],
                "residual": step.residuals.norm_l1,
                "path_step_id": step.step_id,
                "input_state_id": step.input_state_id,
                "output_state_id": step.output_state_id,
                "representation_before": list(step.representation_before),
                "representation_after": list(step.representation_after),
                "resource_cost": asdict(step.cost),
                "uncertainty_delta": step.uncertainty_delta,
                "historical_causation_claim": False,
            },
            units={"residual": "1"},
            uncertainty={"model": step.uncertainty_after},
        )
        events.append(event)
        parent = event

    experiment = DiscoveryEvent.create(
        "ExperimentSpec",
        subject_id,
        next(timestamps),
        parent_ids=(parent.event_id,),
        provenance=path.source_ids,
        status="candidate",
        payload={
            "protocol": "Run DiscoveryPath structural/OAK audit and compare against adversarial path baselines.",
            "success_criteria": "all structural gates pass without target/future evidence leakage",
            "rollback": "quarantine the path model; preserve negative memory and original inputs",
            "path_id": path.path_id,
        },
    )
    result = DiscoveryEvent.create(
        "ResultPacket",
        subject_id,
        next(timestamps),
        parent_ids=(experiment.event_id,),
        provenance=path.source_ids,
        status="candidate",
        payload={
            "success": True,
            "title": "DiscoveryPath structural model result",
            "protocol": "DiscoveryPath R0.4 software gates",
            "baseline": "counter-path/adversarial branch",
            "path_lineage_hash": path.lineage_hash,
            "historical_truth_certified": False,
        },
        units={"path_cost": "1", "residual_budget": "1"},
        uncertainty={"terminal_model_uncertainty": path.terminal_state.uncertainty},
    )
    oak = DiscoveryEvent.create(
        "OAKTransition",
        subject_id,
        next(timestamps),
        parent_ids=(result.event_id,),
        provenance=path.source_ids,
        status="candidate",
        payload={
            "from_status": "IDEA",
            "to_status": "IMPLEMENTED",
            "cause": "DiscoveryPath IR encoded and software-gated; no historical/scientific certification implied.",
        },
    )
    events.extend((experiment, result, oak))
    return tuple(events)


def validate_bridge_events(path: DiscoveryPath) -> BridgeReceipt:
    events = path_to_kernel_events(path)
    seen: set[str] = set()
    parentage_valid = True
    issues: list[str] = []
    for event in events:
        unknown_parents = [parent for parent in event.parent_ids if parent not in seen]
        if unknown_parents:
            parentage_valid = False
            issues.append(f"{event.event_id}: parents not previously emitted: {unknown_parents}")
        issues.extend(event.validate())
        seen.add(event.event_id)
    return BridgeReceipt(
        path_id=path.path_id,
        event_ids=tuple(event.event_id for event in events),
        event_types=tuple(event.event_type for event in events),
        parentage_valid=parentage_valid,
        contracts_valid=parentage_valid and not issues,
        validation_issues=tuple(issues),
    )
