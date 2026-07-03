"""Query and canon utilities for Omega Universal Absorber outputs.

This module reads the artifacts emitted by ``omega-corpus-absorb`` and turns
raw chunks/claim candidates into searchable, OAK-safe work packets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class QueryHit:
    kind: str
    identifier: str
    path: str
    score: float
    text: str
    oak_gate: str = "candidate"


@dataclass(frozen=True)
class CanonPacket:
    packet_id: str
    title: str
    status: str
    oak_gate: str
    source_paths: tuple[str, ...]
    claims: tuple[str, ...]
    tests_to_build: tuple[str, ...]
    mminus: tuple[str, ...]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_absorber_output(output_dir: str | Path) -> dict:
    root = Path(output_dir)
    return {
        "root": str(root),
        "manifest": json.loads((root / "manifest.json").read_text(encoding="utf-8")) if (root / "manifest.json").exists() else {},
        "chunks": load_jsonl(root / "chunks.jsonl"),
        "claims": load_jsonl(root / "claims.jsonl"),
        "oak_report": json.loads((root / "oak_report.json").read_text(encoding="utf-8")) if (root / "oak_report.json").exists() else {},
    }


def tokenize(query: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[\wÀ-ÿΩω⁺⁻-]+", query) if len(token) > 1]


def score_text(text: str, terms: Sequence[str]) -> float:
    lowered = text.lower()
    if not terms:
        return 0.0
    hits = sum(lowered.count(term) for term in terms)
    coverage = sum(1 for term in terms if term in lowered) / len(terms)
    return round(hits * 0.25 + coverage, 4)


def search_output(output_dir: str | Path, query: str, *, limit: int = 10) -> list[QueryHit]:
    payload = load_absorber_output(output_dir)
    terms = tokenize(query)
    hits: list[QueryHit] = []
    for chunk in payload["chunks"]:
        score = score_text(chunk.get("text", ""), terms)
        if score > 0:
            hits.append(
                QueryHit(
                    kind="chunk",
                    identifier=chunk.get("chunk_id", ""),
                    path=chunk.get("path", ""),
                    score=score,
                    text=chunk.get("text", "")[:700],
                    oak_gate="raw_extraction_not_proof",
                )
            )
    for claim in payload["claims"]:
        score = score_text(claim.get("text", ""), terms) + float(claim.get("confidence", 0.0))
        if score > 0:
            hits.append(
                QueryHit(
                    kind="claim",
                    identifier=claim.get("claim_id", ""),
                    path=claim.get("path", ""),
                    score=round(score, 4),
                    text=claim.get("text", "")[:700],
                    oak_gate=claim.get("oak_gate", "candidate"),
                )
            )
    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]


def render_hits_markdown(hits: Sequence[QueryHit]) -> str:
    if not hits:
        return "# Omega Absorber Search\n\nNo hits.\n"
    lines = ["# Omega Absorber Search", ""]
    for index, hit in enumerate(hits, start=1):
        lines.extend(
            [
                f"## {index}. {hit.kind} `{hit.identifier}`",
                "",
                f"- path: `{hit.path}`",
                f"- score: `{hit.score}`",
                f"- OAK: `{hit.oak_gate}`",
                "",
                hit.text.replace("\n", " ")[:700],
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_canon_packets(output_dir: str | Path, *, max_packets: int = 20) -> list[CanonPacket]:
    payload = load_absorber_output(output_dir)
    claims = sorted(payload["claims"], key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
    packets: list[CanonPacket] = []
    for claim in claims[:max_packets]:
        risk_flags = tuple(claim.get("risk_flags", ()))
        oak_gate = claim.get("oak_gate", "candidate_needs_evidence")
        title = claim.get("text", "claim")[:72].replace("\n", " ").strip() or "claim"
        tests = (
            "Find source evidence and counter-evidence for this claim.",
            "Define measurable inputs, outputs, invariants, and failure modes.",
            "Create the smallest reproducible benchmark or proof obligation.",
        )
        mminus = tuple(f"risk:{flag}" for flag in risk_flags) or ("not_yet_validated",)
        packets.append(
            CanonPacket(
                packet_id=claim.get("claim_id", ""),
                title=title,
                status=claim.get("status", "exploratory"),
                oak_gate=oak_gate,
                source_paths=(claim.get("path", ""),),
                claims=(claim.get("text", ""),),
                tests_to_build=tests,
                mminus=mminus,
            )
        )
    return packets


def write_canon_packets(output_dir: str | Path, packets: Sequence[CanonPacket]) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "canon_packets.jsonl"
    path.write_text("".join(json.dumps(asdict(packet), ensure_ascii=False) + "\n" for packet in packets), encoding="utf-8")
    return path


def render_canon_markdown(packets: Sequence[CanonPacket]) -> str:
    lines = ["# Omega Absorber Canon Packets", "", "Status: candidates only; OAK validation required before canonization.", ""]
    for packet in packets:
        lines.extend(
            [
                f"## {packet.title}",
                "",
                f"- packet: `{packet.packet_id}`",
                f"- status: `{packet.status}`",
                f"- OAK: `{packet.oak_gate}`",
                f"- sources: {', '.join(f'`{source}`' for source in packet.source_paths)}",
                "- tests:",
            ]
        )
        lines.extend(f"  - {test}" for test in packet.tests_to_build)
        lines.append("- M⁻:")
        lines.extend(f"  - {item}" for item in packet.mminus)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-absorb-query", description="Search and canonize absorber outputs")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("output_dir")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    canon = sub.add_parser("canon")
    canon.add_argument("output_dir")
    canon.add_argument("--max-packets", type=int, default=20)
    canon.add_argument("--write", action="store_true")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> str:
    args = build_parser().parse_args(argv)
    if args.command == "search":
        return render_hits_markdown(search_output(args.output_dir, args.query, limit=args.limit))
    packets = build_canon_packets(args.output_dir, max_packets=args.max_packets)
    if args.write:
        path = write_canon_packets(args.output_dir, packets)
        return f"canon_packets={len(packets)} path={path}\n"
    return render_canon_markdown(packets)


def main() -> None:
    sys.stdout.write(run_cli())


if __name__ == "__main__":
    main()
