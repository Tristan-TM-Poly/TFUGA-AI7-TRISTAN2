from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from .core import Envelope

BRIDGE_BOUNDARY = "snapshot_bridge != semantic_equivalence_or_external_validation"


def adapt_capability(capability: Any, *, provenance: tuple[str, ...] = ()) -> Envelope:
    """Reuse Ω-CAPABILITY-OS Capability without creating a second ontology."""
    capability_id = getattr(capability, "capability_id", None)
    if not capability_id:
        raise TypeError("capability must expose capability_id")
    if is_dataclass(capability):
        payload = asdict(capability)
    else:
        payload = {
            key: getattr(capability, key)
            for key in (
                "capability_id", "domains", "consumes", "produces", "authority",
                "quality", "information_gain", "verifiability", "reuse", "cost",
                "latency", "risk", "alternatives", "failure_modes",
            )
            if hasattr(capability, key)
        }
    payload["source_ontology"] = "omega_capability_os_t.core.Capability"
    return Envelope(
        graph="capability",
        object_type="capability",
        object_id=str(capability_id),
        payload=payload,
        provenance=provenance,
        uncertainty=0.0,
        authority=str(payload.get("authority", "read")),
        oak_state="UNKNOWN",
    )


def adapt_snapshot(
    *,
    component: str,
    graph: str,
    object_type: str,
    object_id: str,
    payload: Mapping[str, Any],
    provenance: tuple[str, ...] = (),
    uncertainty: float = 0.0,
    oak_state: str = "UNKNOWN",
) -> Envelope:
    """Adapter boundary for independent PR stacks.

    It accepts declared snapshots from Discovery/Cognitive/Compute/GreatSages/etc.
    The ABI does not import or certify those branches.
    """
    body = dict(payload)
    body["source_component"] = component
    body["bridge_boundary"] = BRIDGE_BOUNDARY
    return Envelope(
        graph=graph,
        object_type=object_type,
        object_id=object_id,
        payload=body,
        provenance=provenance,
        uncertainty=uncertainty,
        oak_state=oak_state,
    )


def component_manifest() -> dict[str, dict[str, str]]:
    return {
        "github_memory": {
            "pr": "#447",
            "mode": "native_stacked_base",
            "boundary": "candidate_reuse != verified_reuse",
        },
        "greatsages_tensor": {
            "pr": "#443",
            "mode": "snapshot_adapter",
            "boundary": BRIDGE_BOUNDARY,
        },
        "discovery_os": {
            "pr": "#444",
            "mode": "snapshot_adapter",
            "boundary": BRIDGE_BOUNDARY,
        },
        "compute_physics": {
            "pr": "#445",
            "mode": "snapshot_adapter",
            "boundary": BRIDGE_BOUNDARY,
        },
        "cognitive_computer": {
            "pr": "#446",
            "mode": "snapshot_adapter",
            "boundary": BRIDGE_BOUNDARY,
        },
    }
