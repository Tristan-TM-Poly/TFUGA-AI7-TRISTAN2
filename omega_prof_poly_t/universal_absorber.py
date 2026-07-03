"""Omega Universal Absorber.

OAK-safe ingestion engine for Tristan corpora.

The module deliberately stays dependency-light. It can ingest plain text,
Markdown, JSON, Python/code, ZIP archives, and PDFs when an optional PDF text
extractor is installed. Every extracted fragment keeps provenance and confidence
metadata so the downstream HGFM/CVCD/OAK layers can distinguish raw extraction,
inference, claim, evidence, residual, and publishable canon.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".py",
    ".toml",
    ".tex",
    ".csv",
}
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".sql",
    ".html",
    ".css",
}
CLAIM_PATTERNS = (
    "theory",
    "theorem",
    "hypothesis",
    "claim",
    "conjecture",
    "proof",
    "prototype",
    "oak",
    "cvcd",
    "hgfm",
    "système",
    "théorie",
    "preuve",
    "hypothèse",
    "protocole",
)
RISK_PATTERNS = (
    "patent",
    "brevet",
    "secret",
    "confidential",
    "privé",
    "proprietary",
    "medical",
    "diagnostic",
    "laser",
    "high voltage",
    "haute tension",
    "danger",
    "explosive",
    "biohazard",
    "personal data",
    "données personnelles",
)


@dataclass(frozen=True)
class SourceObject:
    """A discovered file-like object before extraction."""

    source_id: str
    path: str
    suffix: str
    sha256: str
    size_bytes: int
    container: str | None = None


@dataclass(frozen=True)
class Chunk:
    """Smallest OAK-traceable text unit emitted by the absorber."""

    chunk_id: str
    source_id: str
    path: str
    text: str
    page: int | None = None
    offset: int = 0
    char_count: int = 0
    token_estimate: int = 0
    extraction_confidence: float = 1.0
    extraction_method: str = "text"
    role: str = "raw_extraction"
    tags: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClaimCandidate:
    claim_id: str
    chunk_id: str
    source_id: str
    path: str
    text: str
    confidence: float
    status: str
    oak_gate: str
    evidence_level: str
    risk_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class HyperEdge:
    edge_id: str
    kind: str
    nodes: tuple[str, ...]
    weight: float = 1.0
    evidence: tuple[str, ...] = ()


@dataclass
class AbsorbResult:
    manifest: dict
    chunks: list[Chunk] = field(default_factory=list)
    claims: list[ClaimCandidate] = field(default_factory=list)
    hyperedges: list[HyperEdge] = field(default_factory=list)
    oak_report: dict = field(default_factory=dict)

    def to_json_dict(self) -> dict:
        return {
            "manifest": self.manifest,
            "chunks": [asdict(chunk) for chunk in self.chunks],
            "claims": [asdict(claim) for claim in self.claims],
            "hyperedges": [asdict(edge) for edge in self.hyperedges],
            "oak_report": self.oak_report,
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def split_text(text: str, *, max_chars: int = 2500, overlap: int = 250) -> list[tuple[int, str]]:
    """Split text into overlapping chunks while preserving offsets."""

    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [(0, text)]

    chunks: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        window = text[start:end]
        if end < len(text):
            breakpoints = [window.rfind("\n\n"), window.rfind(". "), window.rfind("; ")]
            cut = max(breakpoints)
            if cut > max_chars * 0.45:
                end = start + cut + 1
                window = text[start:end]
        chunks.append((start, window.strip()))
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def iter_source_objects(path: Path) -> Iterable[tuple[SourceObject, bytes]]:
    """Yield source objects from a file, directory, or ZIP archive."""

    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file():
                data = child.read_bytes()
                rel = str(child.relative_to(path))
                yield SourceObject(
                    source_id=stable_id("src", rel, sha256_bytes(data)),
                    path=rel,
                    suffix=child.suffix.lower(),
                    sha256=sha256_bytes(data),
                    size_bytes=len(data),
                ), data
        return

    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith("/"):
                    continue
                data = archive.read(name)
                yield SourceObject(
                    source_id=stable_id("src", path.name, name, sha256_bytes(data)),
                    path=name,
                    suffix=Path(name).suffix.lower(),
                    sha256=sha256_bytes(data),
                    size_bytes=len(data),
                    container=str(path),
                ), data
        return

    yield SourceObject(
        source_id=stable_id("src", path.name, sha256_bytes(data)),
        path=path.name,
        suffix=suffix,
        sha256=sha256_bytes(data),
        size_bytes=len(data),
    ), data


def extract_pdf_text(data: bytes, source: SourceObject) -> tuple[str, float, str, tuple[str, ...]]:
    """Best-effort PDF text extraction with optional pypdf.

    The absorber records low confidence when PDF text extraction is unavailable.
    OCR is intentionally not automatic here because it is expensive, lossy, and
    should run as a separate OAK-traceable stage.
    """

    try:
        import pypdf  # type: ignore
        from io import BytesIO

        reader = pypdf.PdfReader(BytesIO(data))
        pages: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            pages.append(f"\n\n[[page={index}]]\n{page_text}")
        text = normalize_text("\n".join(pages))
        confidence = 0.88 if text else 0.25
        warnings = () if text else ("pdf_no_extractable_text_possible_scan",)
        return text, confidence, "pypdf", warnings
    except Exception as exc:  # pragma: no cover - optional dependency path
        return (
            "",
            0.10,
            "pdf_unavailable",
            (f"pdf_text_extraction_unavailable:{type(exc).__name__}",),
        )


def extract_text(data: bytes, source: SourceObject) -> tuple[str, float, str, tuple[str, ...]]:
    if source.suffix == ".pdf":
        return extract_pdf_text(data, source)
    if source.suffix in TEXT_EXTENSIONS or source.suffix in CODE_EXTENSIONS:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return normalize_text(data.decode(encoding)), 0.98, f"decode:{encoding}", ()
            except UnicodeDecodeError:
                continue
        return "", 0.10, "decode_failed", ("text_decode_failed",)
    return "", 0.0, "unsupported", ("unsupported_file_type",)


def tags_for_text(path: str, text: str, suffix: str) -> tuple[str, ...]:
    lowered = f"{path}\n{text[:3000]}".lower()
    tags: set[str] = set()
    if suffix == ".pdf":
        tags.add("pdf")
    if suffix in CODE_EXTENSIONS:
        tags.add("code")
    if any(term in lowered for term in ("oak", "risk", "résidu", "residue", "falsif")):
        tags.add("oak")
    if any(term in lowered for term in ("hgfm", "hypergraph", "hypergraphe")):
        tags.add("hgfm")
    if any(term in lowered for term in ("cvcd", "compression", "decompression", "décompression")):
        tags.add("cvcd")
    if any(term in lowered for term in ("patent", "brevet", "ip", "licence", "license")):
        tags.add("ip")
    if any(term in lowered for term in ("prototype", "mvp", "benchmark", "test")):
        tags.add("prototype")
    return tuple(sorted(tags))


def build_chunks(source: SourceObject, text: str, confidence: float, method: str, warnings: tuple[str, ...]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for index, (offset, chunk_text) in enumerate(split_text(text)):
        page_match = re.search(r"\[\[page=(\d+)\]\]", chunk_text)
        page = int(page_match.group(1)) if page_match else None
        chunk_id = stable_id("chk", source.source_id, index, offset, chunk_text[:128])
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source_id=source.source_id,
                path=source.path,
                text=chunk_text,
                page=page,
                offset=offset,
                char_count=len(chunk_text),
                token_estimate=max(1, math.ceil(len(chunk_text) / 4)),
                extraction_confidence=confidence,
                extraction_method=method,
                tags=tags_for_text(source.path, chunk_text, source.suffix),
                warnings=warnings,
            )
        )
    if not chunks and warnings:
        chunks.append(
            Chunk(
                chunk_id=stable_id("chk", source.source_id, "empty"),
                source_id=source.source_id,
                path=source.path,
                text="",
                char_count=0,
                token_estimate=0,
                extraction_confidence=confidence,
                extraction_method=method,
                tags=tags_for_text(source.path, "", source.suffix),
                warnings=warnings,
            )
        )
    return chunks


def risk_flags_for_text(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    flags = [pattern for pattern in RISK_PATTERNS if pattern in lowered]
    return tuple(sorted(set(flags)))


def claim_score(text: str) -> float:
    lowered = text.lower()
    hits = sum(1 for pattern in CLAIM_PATTERNS if pattern in lowered)
    equation_bonus = 1 if re.search(r"[=⇒→∂∇∑∫]", text) else 0
    citation_bonus = 1 if re.search(r"\b(arxiv|doi|pdb|github|http|isbn)\b", lowered) else 0
    return min(1.0, 0.20 + 0.14 * hits + 0.10 * equation_bonus + 0.08 * citation_bonus)


def extract_claims(chunks: Sequence[Chunk]) -> list[ClaimCandidate]:
    claims: list[ClaimCandidate] = []
    for chunk in chunks:
        if not chunk.text.strip():
            continue
        score = claim_score(chunk.text)
        if score < 0.34:
            continue
        risk_flags = risk_flags_for_text(chunk.text)
        oak_gate = "blocked_ip_or_safety_review" if risk_flags else "candidate_needs_evidence"
        evidence_level = "raw_claim_candidate"
        status = "exploratory"
        excerpt = chunk.text[:900].strip()
        claims.append(
            ClaimCandidate(
                claim_id=stable_id("clm", chunk.chunk_id, score, excerpt[:64]),
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                path=chunk.path,
                text=excerpt,
                confidence=round(min(score, chunk.extraction_confidence), 3),
                status=status,
                oak_gate=oak_gate,
                evidence_level=evidence_level,
                risk_flags=risk_flags,
            )
        )
    return claims


def build_hyperedges(chunks: Sequence[Chunk], claims: Sequence[ClaimCandidate]) -> list[HyperEdge]:
    edges: list[HyperEdge] = []
    chunks_by_source: dict[str, list[str]] = {}
    for chunk in chunks:
        chunks_by_source.setdefault(chunk.source_id, []).append(chunk.chunk_id)
        for tag in chunk.tags:
            edges.append(
                HyperEdge(
                    edge_id=stable_id("edge", "tag", tag, chunk.chunk_id),
                    kind="chunk_has_tag",
                    nodes=(chunk.chunk_id, f"tag:{tag}"),
                    weight=0.55,
                    evidence=(chunk.chunk_id,),
                )
            )
    for source_id, node_ids in chunks_by_source.items():
        if node_ids:
            edges.append(
                HyperEdge(
                    edge_id=stable_id("edge", "source", source_id),
                    kind="source_contains_chunks",
                    nodes=tuple([source_id, *node_ids[:256]]),
                    weight=1.0,
                    evidence=tuple(node_ids[:32]),
                )
            )
    for claim in claims:
        edges.append(
            HyperEdge(
                edge_id=stable_id("edge", "claim", claim.claim_id, claim.chunk_id),
                kind="claim_candidate_from_chunk",
                nodes=(claim.claim_id, claim.chunk_id, claim.source_id),
                weight=claim.confidence,
                evidence=(claim.chunk_id,),
            )
        )
        for risk in claim.risk_flags:
            edges.append(
                HyperEdge(
                    edge_id=stable_id("edge", "risk", claim.claim_id, risk),
                    kind="claim_has_risk_flag",
                    nodes=(claim.claim_id, f"risk:{risk}"),
                    weight=0.9,
                    evidence=(claim.chunk_id,),
                )
            )
    return edges


def oak_report_for(objects: Sequence[SourceObject], chunks: Sequence[Chunk], claims: Sequence[ClaimCandidate]) -> dict:
    blocked = [claim for claim in claims if claim.risk_flags]
    warnings = sorted({warning for chunk in chunks for warning in chunk.warnings})
    return {
        "status": "dry_run_only",
        "publishable": False,
        "source_objects": len(objects),
        "chunks": len(chunks),
        "claim_candidates": len(claims),
        "blocked_or_review_claims": len(blocked),
        "warnings": warnings,
        "gates": [
            "raw extraction is not proof",
            "PDF/OCR extraction requires page-level audit before canonization",
            "IP/brevet/confidential content must remain private until triage",
            "medical/safety/high-voltage/laser claims require human expert review",
            "generated hypergraph edges are candidate links until evidence is checked",
        ],
    }


def absorb_path(path: str | Path) -> AbsorbResult:
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(root)
    objects: list[SourceObject] = []
    chunks: list[Chunk] = []
    for source, data in iter_source_objects(root):
        objects.append(source)
        text, confidence, method, warnings = extract_text(data, source)
        chunks.extend(build_chunks(source, text, confidence, method, warnings))
    claims = extract_claims(chunks)
    hyperedges = build_hyperedges(chunks, claims)
    manifest = {
        "schema": "omega_absorber_manifest_v1",
        "input": str(root),
        "mode": "dry_run_oak_safe",
        "objects": [asdict(source) for source in objects],
    }
    return AbsorbResult(
        manifest=manifest,
        chunks=chunks,
        claims=claims,
        hyperedges=hyperedges,
        oak_report=oak_report_for(objects, chunks, claims),
    )


def graphml_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_graphml(result: AbsorbResult) -> str:
    nodes: dict[str, dict[str, object]] = {}
    for source in result.manifest.get("objects", []):
        nodes[source["source_id"]] = {"kind": "source", "label": source["path"]}
    for chunk in result.chunks:
        nodes[chunk.chunk_id] = {"kind": "chunk", "label": chunk.path, "tokens": chunk.token_estimate}
        for tag in chunk.tags:
            nodes[f"tag:{tag}"] = {"kind": "tag", "label": tag}
    for claim in result.claims:
        nodes[claim.claim_id] = {"kind": "claim", "label": claim.text[:80], "confidence": claim.confidence}
        for risk in claim.risk_flags:
            nodes[f"risk:{risk}"] = {"kind": "risk", "label": risk}
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
        "  <graph edgedefault=\"undirected\">",
    ]
    for node_id, attrs in sorted(nodes.items()):
        label = graphml_escape(attrs.get("label", node_id))
        kind = graphml_escape(attrs.get("kind", "node"))
        lines.append(f"    <node id=\"{graphml_escape(node_id)}\"><data key=\"kind\">{kind}</data><data key=\"label\">{label}</data></node>")
    for edge in result.hyperedges:
        if len(edge.nodes) < 2:
            continue
        source = edge.nodes[0]
        for target in edge.nodes[1:]:
            lines.append(
                f"    <edge id=\"{graphml_escape(edge.edge_id + '_' + target)}\" source=\"{graphml_escape(source)}\" target=\"{graphml_escape(target)}\"><data key=\"kind\">{graphml_escape(edge.kind)}</data><data key=\"weight\">{edge.weight}</data></edge>"
            )
    lines.extend(["  </graph>", "</graphml>"])
    return "\n".join(lines) + "\n"


def write_outputs(result: AbsorbResult, output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "manifest": out / "manifest.json",
        "chunks": out / "chunks.jsonl",
        "claims": out / "claims.jsonl",
        "hypergraph": out / "hypergraph.json",
        "graphml": out / "hypergraph.graphml",
        "oak_report": out / "oak_report.json",
    }
    files["manifest"].write_text(json.dumps(result.manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files["chunks"].write_text("".join(json.dumps(asdict(chunk), ensure_ascii=False) + "\n" for chunk in result.chunks), encoding="utf-8")
    files["claims"].write_text("".join(json.dumps(asdict(claim), ensure_ascii=False) + "\n" for claim in result.claims), encoding="utf-8")
    files["hypergraph"].write_text(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files["graphml"].write_text(render_graphml(result), encoding="utf-8")
    files["oak_report"].write_text(json.dumps(result.oak_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {key: str(path) for key, path in files.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-corpus-absorb", description="OAK-safe universal corpus absorber")
    parser.add_argument("input", help="File, directory, or ZIP archive to absorb")
    parser.add_argument("--output-dir", default="generated/omega_universal_absorber", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Print the full result JSON instead of a compact summary")
    return parser


def run_cli(argv: Sequence[str] | None = None) -> str:
    args = build_parser().parse_args(argv)
    result = absorb_path(args.input)
    files = write_outputs(result, args.output_dir)
    if args.json:
        return json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2) + "\n"
    return (
        "omega-corpus-absorb dry-run complete\n"
        f"objects={result.oak_report['source_objects']} chunks={result.oak_report['chunks']} "
        f"claims={result.oak_report['claim_candidates']} review={result.oak_report['blocked_or_review_claims']}\n"
        + "\n".join(f"{name}={path}" for name, path in files.items())
        + "\n"
    )


def main() -> None:
    try:
        sys.stdout.write(run_cli())
    except Exception as exc:  # pragma: no cover - CLI guard
        sys.stderr.write(f"omega-corpus-absorb error: {exc}\n")
        raise


if __name__ == "__main__":
    main()
