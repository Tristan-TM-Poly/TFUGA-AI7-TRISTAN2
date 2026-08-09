from __future__ import annotations

import re
from typing import Any

from .models import DocumentIR


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return text or "meaning"


def notation_registry(doc: DocumentIR) -> dict[str, Any]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for node in doc.nodes:
        for spec in node.symbols:
            key = (spec.scope, spec.symbol)
            bucket = buckets.setdefault(
                key,
                {
                    "scope": spec.scope,
                    "symbol": spec.symbol,
                    "meanings": set(),
                    "units": set(),
                    "node_ids": set(),
                },
            )
            if spec.meaning.strip():
                bucket["meanings"].add(spec.meaning.strip())
            if spec.unit.strip():
                bucket["units"].add(spec.unit.strip())
            bucket["node_ids"].add(node.id)
    entries = []
    for _, bucket in sorted(buckets.items()):
        entries.append(
            {
                "scope": bucket["scope"],
                "symbol": bucket["symbol"],
                "meanings": sorted(bucket["meanings"]),
                "units": sorted(bucket["units"]),
                "node_ids": sorted(bucket["node_ids"]),
                "collision": len(bucket["meanings"]) > 1 or len(bucket["units"]) > 1,
            }
        )
    return {
        "semantic_hash": doc.semantic_hash(),
        "entries": entries,
        "collision_count": sum(1 for x in entries if x["collision"]),
        "boundary": "notation collisions are review signals; rename proposals do not mutate the source DocumentIR",
    }


def notation_rename_plan(doc: DocumentIR) -> dict[str, Any]:
    registry = notation_registry(doc)
    proposals: list[dict[str, Any]] = []
    for entry in registry["entries"]:
        if not entry["collision"]:
            continue
        meanings = entry["meanings"] or ["unspecified"]
        original = entry["symbol"]
        for index, meaning in enumerate(meanings):
            if index == 0:
                proposed = original
            else:
                suffix = _slug(meaning).replace("-", "")
                if original.startswith("\\"):
                    proposed = rf"{original}_{{\mathrm{{{suffix}}}}}"
                else:
                    proposed = rf"{original}_{{\mathrm{{{suffix}}}}}"
            proposals.append(
                {
                    "scope": entry["scope"],
                    "symbol": original,
                    "meaning": meaning,
                    "proposed_symbol": proposed,
                    "node_ids": entry["node_ids"],
                    "automatic_mutation": False,
                }
            )
    return {
        "semantic_hash": doc.semantic_hash(),
        "proposals": proposals,
        "requires_review": bool(proposals),
        "boundary": "proposal only; notation changes require explicit semantic review",
    }
