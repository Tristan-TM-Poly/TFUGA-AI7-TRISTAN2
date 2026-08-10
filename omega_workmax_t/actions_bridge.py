from __future__ import annotations

from pathlib import Path
from typing import Any


def collect_trigger_hotspots(root: str | Path = ".") -> dict[str, Any]:
    """Reuse Ω-ACTIONS TriggerHotspots when the sibling package is available."""
    try:
        from omega_actions_t.trigger_hotspots import analyze_trigger_hotspots
    except ImportError as exc:  # pragma: no cover - exercised only outside the integrated repository
        raise RuntimeError("omega_actions_t is required for the Actions bridge") from exc
    report = analyze_trigger_hotspots(root)
    return {
        "schema": "omega-workmax-actions-bridge/v1",
        "workflow_count": report["workflow_count"],
        "shared_hotspot_count": len(report["shared_hotspots"]),
        "top_shared_hotspots": report["shared_hotspots"][:20],
        "oak_limits": [
            "Trigger frequency is not dependency proof.",
            "Use Ω-ACTIONS PR-diff and dependency gates before causal promotion.",
        ],
    }
