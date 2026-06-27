from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .schemas import RosetteResult


def source_refs(result: RosetteResult) -> list[dict]:
    refs = []
    seen: set[str] = set()
    for item in [*result.blocks, *result.equations, *[c for c in result.claims if c.source is not None]]:
        src = item.source  # type: ignore[attr-defined]
        sid = src.stable_id()
        if sid not in seen:
            seen.add(sid)
            refs.append(asdict(src))
    return refs


def fidelity_report(result: RosetteResult) -> dict:
    refs = source_refs(result)
    with_page = sum(1 for ref in refs if ref.get("page") is not None)
    with_bbox = sum(1 for ref in refs if ref.get("bbox") is not None)
    with_span = sum(1 for ref in refs if ref.get("span_start") is not None and ref.get("span_end") is not None)
    avg_block_conf = sum(b.confidence for b in result.blocks) / max(1, len(result.blocks))
    return {
        "input_path": result.input_path,
        "sha256": result.sha256,
        "extractor_runs": [asdict(run) for run in result.extractor_runs],
        "counts": {
            "blocks": len(result.blocks),
            "equations": len(result.equations),
            "claims": len(result.claims),
            "source_refs": len(refs),
            "source_refs_with_page": with_page,
            "source_refs_with_bbox": with_bbox,
            "source_refs_with_span": with_span,
        },
        "confidence": {
            "average_block_confidence": round(avg_block_conf, 4),
            "equation_min_confidence": min([e.confidence for e in result.equations], default=0.0),
            "claim_min_confidence": min([c.confidence for c in result.claims], default=0.0),
        },
        "oak_status": "research-usable" if result.blocks and with_span else "uncertain",
        "oak_findings": result.oak_findings,
        "memory_minus": result.memory_minus,
    }


def _yaml_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def theory_capsule_yaml(result: RosetteResult) -> str:
    lines = [
        "theory_capsule:",
        f"  name: {_yaml_scalar(Path(result.input_path).stem)}",
        "  domain: \"unknown/research\"",
        f"  source_sha256: {_yaml_scalar(result.sha256)}",
        "  tristan_links:",
        "    - Ω-ROSETTE-T",
        "    - OAK",
        "    - M⁻",
        "    - HGFM",
        "    - CVCD",
        "  equations:",
    ]
    if result.equations:
        for idx, eq in enumerate(result.equations, 1):
            lines.extend(
                [
                    f"    - id: E{idx}",
                    f"      latex: {_yaml_scalar(eq.latex)}",
                    f"      page: {_yaml_scalar(eq.source.page)}",
                    f"      extractor: {_yaml_scalar(eq.source.extractor)}",
                    f"      oak_status: {_yaml_scalar(eq.oak_status)}",
                ]
            )
    else:
        lines.append("    []")
    lines.append("  claims:")
    if result.claims:
        for idx, claim in enumerate(result.claims, 1):
            lines.extend(
                [
                    f"    - id: C{idx}",
                    f"      text: {_yaml_scalar(claim.claim[:240])}",
                    f"      page: {_yaml_scalar(claim.source.page if claim.source else None)}",
                    f"      oak_status: {_yaml_scalar(claim.oak_status)}",
                    "      evidence_ids: []",
                ]
            )
    else:
        lines.append("    []")
    lines.extend([
        "  oak_gates:",
        "    - source_refs_required",
        "    - render_diff_repair_pending",
        "    - dimensional_oak_pending",
        "    - evidence_links_pending",
    ])
    return "\n".join(lines) + "\n"


def write_fidelity_outputs(result: RosetteResult, out: Path) -> None:
    (out / "source_refs.json").write_text(json.dumps(source_refs(result), indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "fidelity_report.json").write_text(json.dumps(fidelity_report(result), indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "theory_capsule.yaml").write_text(theory_capsule_yaml(result), encoding="utf-8")
