from __future__ import annotations

import hashlib
import json
from typing import Any

from .capability import route_capabilities
from .crystallizer import CrystallizationGovernor
from .graph import WorkHypergraph
from .models import WorkPacket
from .planner import deduplicate_packets, pareto_front, plan_waves
from .telemetry import WorkTelemetryInput, compute_metrics
from .twin import adaptive_worker_sweep, simulate


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    packets = tuple(WorkPacket.from_dict(item) for item in payload.get("packets", []))
    dedup = deduplicate_packets(packets)
    duplicate_ids = set(dedup.duplicate_to_canonical)

    # Dependencies pointing at deduplicated aliases are canonically rewired.
    canonical_packets: list[WorkPacket] = []
    for packet in dedup.unique:
        rewired = tuple(
            dict.fromkeys(dedup.duplicate_to_canonical.get(dep, dep) for dep in packet.dependencies)
        )
        if packet.work_id in rewired:
            rewired = tuple(dep for dep in rewired if dep != packet.work_id)
        data = packet.to_dict()
        data.pop("semantic_signature", None)
        data.pop("content_digest", None)
        data["dependencies"] = rewired
        canonical_packets.append(WorkPacket.from_dict(data))

    graph = WorkHypergraph(canonical_packets)
    workers = int(payload.get("workers", 1))
    waves = plan_waves(graph, workers)
    twin = simulate(graph, workers)
    sweep = adaptive_worker_sweep(graph)

    telemetry_payload = payload.get("telemetry") or {
        "impacted_workunits": len(graph.packets),
        "triggered_jobs": len(graph.packets),
        "started_artifacts": len(packets),
        "crystallized_artifacts": 0,
        "validated_integrated_artifacts": 0,
        "maintained_manual_lines": 1,
        "wall_seconds": twin.wall_seconds,
        "validation_compute_seconds": graph.total_work_seconds,
        "evidence_points": 0,
        "queue_seconds": 0,
        "obsolete_queue_seconds": 0,
        "raw_work_units": len(packets),
        "duplicate_work_units": len(duplicate_ids),
        "mean_quality": 1.0,
    }
    metrics = compute_metrics(WorkTelemetryInput(**telemetry_payload))
    governor = CrystallizationGovernor().decide(
        started=int(telemetry_payload["started_artifacts"]),
        crystallized=int(telemetry_payload["crystallized_artifacts"]),
    )

    capabilities = payload.get("capabilities", [])
    routes = {
        work_id: [match.to_dict() for match in route_capabilities(graph.packets[work_id], capabilities)[:5]]
        for work_id in graph.topological_order
    }

    report: dict[str, Any] = {
        "schema": "omega-workmax-git/v1",
        "status": "OAK_REVIEW_REQUIRED",
        "input_packet_count": len(packets),
        "unique_packet_count": len(graph.packets),
        "duplicate_to_canonical": dedup.duplicate_to_canonical,
        "topological_order": list(graph.topological_order),
        "critical_path": {
            "seconds": graph.critical_path().seconds,
            "work_ids": list(graph.critical_path().work_ids),
        },
        "pareto_front": list(pareto_front(graph)),
        "waves": [wave.to_dict() for wave in waves],
        "twin": twin.to_dict(),
        "adaptive_worker_sweep": [item.to_dict() for item in sweep],
        "metrics": metrics.to_dict(),
        "crystallization_governor": governor.to_dict(),
        "capability_routes": routes,
        "no_permanent_work_count_ceiling": True,
        "automatic_merge_authorized": False,
        "oak_limits": [
            "Scheduling scores are heuristics, not universal value functions.",
            "Lexical capability overlap is a reuse candidate signal, not semantic proof.",
            "Digital-twin timing is prediction until compared with real telemetry.",
            "Fan-out reduction cannot weaken required checks, security, release, provenance, IP, or safety gates.",
            "Logical work amplification is not physical infinite computation.",
            "Remote mutation, merge, deployment, publication, spending, secrets, and irreversible actions remain separately authorized.",
        ],
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    report["report_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
