from __future__ import annotations

from collections import Counter
import re
from typing import Any, Iterable


def canonicalize_atom(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"`[^`]+`", "<entity>", text)
    text = re.sub(r"\b[0-9a-f]{7,64}\b", "<id>", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "<num>", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_primitives(specs: Iterable[dict[str, Any]], min_support: int = 2) -> dict[str, Any]:
    specs = list(specs)
    workflow_counts: Counter[str] = Counter()
    invariant_counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = {}

    for spec in specs:
        name = str(spec.get("name", "unknown"))
        seen_workflow = set()
        seen_invariants = set()
        for step in spec.get("workflow", []):
            atom = canonicalize_atom(str(step))
            seen_workflow.add(atom)
            sources.setdefault(f"workflow::{atom}", set()).add(name)
        for inv in spec.get("invariants", []):
            atom = canonicalize_atom(str(inv))
            seen_invariants.add(atom)
            sources.setdefault(f"invariant::{atom}", set()).add(name)
        workflow_counts.update(seen_workflow)
        invariant_counts.update(seen_invariants)

    workflow = [
        {"atom": atom, "support": count, "skills": sorted(sources[f"workflow::{atom}"])}
        for atom, count in workflow_counts.most_common()
        if count >= min_support
    ]
    invariants = [
        {"atom": atom, "support": count, "skills": sorted(sources[f"invariant::{atom}"])}
        for atom, count in invariant_counts.most_common()
        if count >= min_support
    ]
    return {
        "skill_count": len(specs),
        "min_support": min_support,
        "workflow_primitives": workflow,
        "invariant_primitives": invariants,
        "note": "Lexical/canonical CVCD candidate extraction; semantic equivalence still requires review.",
    }
