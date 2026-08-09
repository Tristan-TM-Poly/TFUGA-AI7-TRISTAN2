"""R0.3 deterministic WorkIR compiler."""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

from .models import WorkPacket, WorkState

def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value))
    return "-".join(part for part in text.split("-") if part) or "root"

def _component(path: str) -> str:
    parts = PurePosixPath(path).parts
    if not parts:
        return "root"
    if parts[0] == ".github" and len(parts) > 1:
        return ".github/" + parts[1]
    return parts[0]

def compile_work_ir(payload: dict[str, Any]) -> dict[str, Any]:
    intent = payload.get("intent") or {}
    intent_id = str(intent.get("id") or "intent")
    objective = str(intent.get("text") or intent.get("objective") or "Compile repository work")
    changed_files = sorted({str(p).replace("\\", "/") for p in payload.get("changed_files", []) if str(p).strip()})
    issues = sorted(payload.get("issues", []), key=lambda x: (int(x.get("number", 0)), str(x.get("title", ""))))
    capabilities = sorted(payload.get("capabilities", []), key=lambda x: str(x.get("capability_id") or x.get("id") or ""))
    residues = sorted(payload.get("oak_residues", []), key=lambda x: str(x.get("residue_id") or x.get("id") or ""))

    packets: list[WorkPacket] = []
    root_id = f"intent:{_slug(intent_id)}"
    packets.append(WorkPacket(
        work_id=root_id,
        objective=objective,
        artifact="workir-intent",
        estimated_seconds=1.0,
        value=float(intent.get("value", 1.0)),
        evidence_weight=0.2,
        crystallization=0.2,
        tags=("intent", "workir"),
        state=WorkState.PLANNED,
    ))

    component_ids: list[str] = []
    grouped: dict[str, list[str]] = {}
    for path in changed_files:
        grouped.setdefault(_component(path), []).append(path)
    for component, paths in sorted(grouped.items()):
        wid = f"delta:{_slug(component)}"
        component_ids.append(wid)
        packets.append(WorkPacket(
            work_id=wid,
            objective=f"Assess changed component {component}",
            artifact="delta-impact",
            dependencies=(root_id,),
            estimated_seconds=max(1.0, float(len(paths))),
            value=0.8,
            evidence_weight=0.7,
            crystallization=0.5,
            reuse_score=0.5,
            risk=0.1,
            tags=("delta", component, *paths),
            required_evidence=("delta-ci",),
            state=WorkState.PLANNED,
        ))

    issue_ids: list[str] = []
    for issue in issues:
        number = int(issue.get("number", 0))
        wid = f"issue:{number or _slug(issue.get('title', 'issue'))}"
        issue_ids.append(wid)
        packets.append(WorkPacket(
            work_id=wid,
            objective=str(issue.get("title") or f"Resolve issue {number}"),
            artifact="issue-resolution-plan",
            dependencies=(root_id,),
            estimated_seconds=float(issue.get("estimated_seconds", 5.0)),
            value=float(issue.get("value", 0.6)),
            evidence_weight=0.5,
            crystallization=0.3,
            risk=float(issue.get("risk", 0.1)),
            tags=("issue", str(number)),
            state=WorkState.PLANNED,
        ))

    capability_ids: list[str] = []
    for cap in capabilities:
        cid = str(cap.get("capability_id") or cap.get("id") or "")
        if not cid:
            continue
        wid = f"capability:{_slug(cid)}"
        capability_ids.append(wid)
        packets.append(WorkPacket(
            work_id=wid,
            objective=f"Evaluate reuse of capability {cid}",
            artifact="capability-route",
            dependencies=(root_id,),
            estimated_seconds=float(cap.get("estimated_seconds", 1.0)),
            value=float(cap.get("value", 0.7)),
            evidence_weight=float(cap.get("evidence_weight", 0.6)),
            crystallization=float(cap.get("crystallization", 0.7)),
            reuse_score=float(cap.get("reuse_score", 0.9)),
            risk=float(cap.get("risk", 0.05)),
            capability_id=cid,
            tags=("capability", cid),
            required_evidence=("capability-contract",),
            state=WorkState.ROUTED,
        ))

    residue_ids: list[str] = []
    for residue in residues:
        rid = str(residue.get("residue_id") or residue.get("id") or "")
        if not rid:
            continue
        wid = f"residue:{_slug(rid)}"
        residue_ids.append(wid)
        packets.append(WorkPacket(
            work_id=wid,
            objective=str(residue.get("objective") or residue.get("description") or f"Resolve OAK residue {rid}"),
            artifact="oak-residue-resolution",
            dependencies=(root_id,),
            estimated_seconds=float(residue.get("estimated_seconds", 3.0)),
            value=float(residue.get("value", 0.9)),
            evidence_weight=0.9,
            crystallization=0.8,
            reuse_score=0.2,
            risk=float(residue.get("risk", 0.2)),
            tags=("oak", "residue", rid),
            required_evidence=tuple(residue.get("required_evidence", ("oak-gate",))),
            state=WorkState.BLOCKED if residue.get("blocking", True) else WorkState.PLANNED,
        ))

    integration_deps = tuple(component_ids + issue_ids + capability_ids + residue_ids) or (root_id,)
    packets.append(WorkPacket(
        work_id=f"integrate:{_slug(intent_id)}",
        objective="Integrate validated work and produce promotion evidence",
        artifact="integration-candidate",
        dependencies=integration_deps,
        estimated_seconds=2.0,
        value=1.0,
        evidence_weight=1.0,
        crystallization=1.0,
        reuse_score=0.8,
        risk=0.1,
        tags=("integration", "crystallization"),
        required_evidence=("tests", "rollback", "promotion-gate"),
        state=WorkState.PLANNED,
    ))

    out = {
        "schema": "omega-workmax-workir/v1",
        "intent_id": intent_id,
        "changed_files": changed_files,
        "packet_count": len(packets),
        "packets": [packet.to_dict() for packet in packets],
        "source_counts": {
            "changed_components": len(component_ids),
            "issues": len(issue_ids),
            "capabilities": len(capability_ids),
            "oak_residues": len(residue_ids),
        },
        "automatic_execution_authorized": False,
        "oak_limits": [
            "WorkIR compilation structures declared inputs; it does not prove task completeness.",
            "Issue priority, capability reuse and residue severity remain evidence-dependent.",
            "The compiler emits plans only and performs no GitHub mutation.",
        ],
    }
    canonical = json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    out["workir_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return out
