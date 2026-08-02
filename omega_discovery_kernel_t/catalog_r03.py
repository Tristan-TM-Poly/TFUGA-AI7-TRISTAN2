"""R0.3 correction for the canonical Ω64 event catalog.

R0.2 referenced ``ResultPacket`` throughout the graph while omitting it from
the 64 registered contracts. R0.3 restores the core-loop result event and moves
sensitivity sweeps to an experiment subtype inside
``ExperimentSpec``/``ResultPacket`` payloads.

Some R0.2 modules imported the original catalog directly. During migration this
module synchronizes those legacy module globals to the corrected immutable
contract so every import path observes the same Ω64 registry.
"""
from __future__ import annotations

from . import catalog as _legacy_catalog
from .catalog import EVENT_CATALOG as R02_EVENT_CATALOG, EventTypeSpec


RESULT_PACKET_SPEC = EventTypeSpec(
    name="ResultPacket",
    family="experiment",
    purpose=(
        "Record the outcome of a simulation, measurement, forecast, baseline "
        "comparison, ablation, sensitivity sweep, or replication with units, "
        "uncertainty, scope, protocol, and success criteria."
    ),
    required_parent_any=(
        "ExperimentSpec",
        "SimulationRun",
        "MeasurementRun",
        "ForecastEvent",
        "BaselineComparison",
        "AblationRun",
        "ReplicationEvent",
    ),
    required_payload=("success",),
    requires_human_approval=False,
    reversible_default=True,
    scientific_gate="result_is_scoped_to_protocol_not_universal_truth",
)

# Sensitivity remains representable as a declared experiment/result subtype;
# ResultPacket is indispensable to the eight-event closed loop and must be a
# first-class contract. The replacement keeps Ω64 exact rather than silently
# growing to 65 names.
EVENT_CATALOG: tuple[EventTypeSpec, ...] = tuple(
    RESULT_PACKET_SPEC if spec.name == "SensitivityRun" else spec
    for spec in R02_EVENT_CATALOG
)
EVENT_SPEC_BY_NAME = {spec.name: spec for spec in EVENT_CATALOG}
EVENT_TYPES = tuple(spec.name for spec in EVENT_CATALOG)
EVENT_FAMILIES = tuple(dict.fromkeys(spec.family for spec in EVENT_CATALOG))


def event_spec(name: str) -> EventTypeSpec:
    try:
        return EVENT_SPEC_BY_NAME[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported discovery event type: {name}") from exc


def catalog_manifest() -> dict[str, object]:
    return {
        "schema": "omega_discovery_kernel.event_catalog.v0.3",
        "event_type_count": len(EVENT_CATALOG),
        "family_count": len(EVENT_FAMILIES),
        "families": list(EVENT_FAMILIES),
        "events": [spec.to_dict() for spec in EVENT_CATALOG],
        "migration": {
            "restored_first_class_event": "ResultPacket",
            "demoted_to_payload_subtype": "SensitivityRun",
            "reason": "all eight core-loop events must be canonical contracts",
            "negative_memory": (
                "Never allow internal references to an event type that is absent "
                "from the machine-readable catalog."
            ),
            "legacy_import_paths_synchronized": True,
        },
        "oak_boundary": (
            "Catalog membership defines a workflow contract, not scientific truth, "
            "causal validity, safety certification, patentability, or market value."
        ),
    }


def _synchronize_legacy_import_paths() -> None:
    """Make modules importing ``.catalog`` observe the corrected R0.3 registry."""

    _legacy_catalog.EVENT_CATALOG = EVENT_CATALOG
    _legacy_catalog.EVENT_SPEC_BY_NAME = EVENT_SPEC_BY_NAME
    _legacy_catalog.EVENT_TYPES = EVENT_TYPES
    _legacy_catalog.EVENT_FAMILIES = EVENT_FAMILIES
    _legacy_catalog.event_spec = event_spec
    _legacy_catalog.catalog_manifest = catalog_manifest


_synchronize_legacy_import_paths()

assert len(EVENT_CATALOG) == 64
assert len(EVENT_SPEC_BY_NAME) == 64
assert len(EVENT_FAMILIES) == 8
assert "ResultPacket" in EVENT_TYPES
assert "SensitivityRun" not in EVENT_TYPES
assert _legacy_catalog.event_spec("ResultPacket") == RESULT_PACKET_SPEC
