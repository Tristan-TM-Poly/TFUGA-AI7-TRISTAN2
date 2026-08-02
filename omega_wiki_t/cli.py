from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .core import MediaWikiClient, MediaWikiError, WikiCompiler
from .theory_hypergraph import TheoryHypergraphBuilder


def _language_list(raw: str) -> list[str] | str:
    if raw.strip().lower() == "all":
        return "all"
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-wiki",
        description="Ω-WIKI-T∞ multilingual evidence and theory hypergraph compiler.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    read = sub.add_parser("read", help="Resolve and summarize one Wikipedia page.")
    read.add_argument("topic")
    read.add_argument("--lang", default="fr")

    languages = sub.add_parser("languages", help="List interlanguage page mappings.")
    languages.add_argument("topic")
    languages.add_argument("--lang", default="fr")

    compile_cmd = sub.add_parser("compile", help="Compile a multilingual evidence bundle.")
    compile_cmd.add_argument("topic")
    compile_cmd.add_argument("--lang", default="fr", help="Source Wikipedia language code.")
    compile_cmd.add_argument("--langs", default="en", help="Comma-separated target languages or 'all'.")
    compile_cmd.add_argument("--max-languages", type=int, default=20, help="Safety cap for --langs all; 0 disables the cap.")
    compile_cmd.add_argument("--output-dir", default="generated/omega_wiki_t")

    theory = sub.add_parser("absorb-theory", help="Absorb repository canon into a useful knowledge hypergraph.")
    theory.add_argument(
        "--canon-json",
        default="interfaces/chatgpt-tristan-v2/data/theory-canon.json",
        help="Structured theory canon JSON.",
    )
    theory.add_argument(
        "--master-canon",
        default="docs/00_MASTER_CANON_TFUGA_AI7_AIT.md",
        help="Master Canon Markdown file.",
    )
    theory.add_argument(
        "--system-index",
        default="MASTER_SYSTEM_INDEX.md",
        help="Ranked Master System Index Markdown file.",
    )
    theory.add_argument(
        "--output-dir",
        default="generated/omega_wiki_t/theory-canon-r0-2",
        help="Output directory for JSON, JSONL, GraphML, and Markdown views.",
    )

    audit = sub.add_parser("audit", help="Audit a previously generated bundle.")
    audit.add_argument("bundle")
    return parser


def _read(topic: str, language: str) -> int:
    client = MediaWikiClient(language)
    page = client.resolve(topic)
    revision = (page.get("revisions") or [{}])[0]
    result = {
        "language": language,
        "requested_title": topic,
        "canonical_title": page.get("title"),
        "qid": (page.get("pageprops") or {}).get("wikibase_item"),
        "canonical_url": page.get("canonicalurl") or page.get("fullurl"),
        "revision_id": revision.get("revid"),
        "revision_timestamp": revision.get("timestamp"),
        "language_count": len(page.get("langlinks") or []),
        "oak_status": "metadata_resolved_not_fact_checked",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _languages(topic: str, language: str) -> int:
    page = MediaWikiClient(language).resolve(topic)
    mappings = {
        item.get("lang"): item.get("title") or item.get("*")
        for item in page.get("langlinks") or []
        if item.get("lang")
    }
    print(json.dumps(dict(sorted(mappings.items())), ensure_ascii=False, indent=2))
    return 0


def _compile(args: argparse.Namespace) -> int:
    max_languages = None if args.max_languages == 0 else args.max_languages
    result = WikiCompiler().compile(
        args.topic,
        source_language=args.lang,
        target_languages=_language_list(args.langs),
        max_languages=max_languages,
    )
    output = WikiCompiler.write(result, args.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(output),
                "qid": result.qid,
                "languages": [article.language for article in result.articles],
                "claim_candidates": len(result.claims),
                "source_links": len(result.sources),
                "missing_languages": list(result.missing_languages),
                "oak_status": "R0.1_READ_ONLY_EXTRACTION_SCAFFOLD_NOT_VERIFICATION",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _absorb_theory(args: argparse.Namespace) -> int:
    graph = TheoryHypergraphBuilder.from_files(
        theory_canon_json=args.canon_json,
        master_canon=args.master_canon,
        system_index=args.system_index,
    )
    output = TheoryHypergraphBuilder.write(graph, args.output_dir)
    systems = [node for node in graph.nodes if node.kind == "theory_system"]
    print(
        json.dumps(
            {
                "output_dir": str(output),
                "nodes": len(graph.nodes),
                "theory_systems": len(systems),
                "hyperedges": len(graph.hyperedges),
                "top_useful_systems": [node.label for node in systems[:10]],
                "oak_status": graph.manifest["oak_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _audit(bundle: str) -> int:
    root = Path(bundle)
    required = ["manifest.json", "articles.jsonl", "claims.jsonl", "sources.jsonl", "language-matrix.json", "report.md"]
    missing = [name for name in required if not (root / name).is_file()]
    issues: list[str] = []

    source_ids: set[str] = set()
    if (root / "sources.jsonl").is_file():
        for line in (root / "sources.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                source_ids.add(str(json.loads(line)["source_id"]))

    claim_count = 0
    orphan_source_ids: set[str] = set()
    if (root / "claims.jsonl").is_file():
        for line in (root / "claims.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            claim_count += 1
            claim = json.loads(line)
            orphan_source_ids.update(set(claim.get("source_ids", [])) - source_ids)

    if orphan_source_ids:
        issues.append(f"orphan source ids: {sorted(orphan_source_ids)}")
    if missing:
        issues.append(f"missing files: {missing}")

    status = "PASS_WITH_R0_1_LIMITS" if not issues else "FAIL"
    print(
        json.dumps(
            {
                "bundle": str(root),
                "status": status,
                "claim_count": claim_count,
                "source_count": len(source_ids),
                "issues": issues,
                "boundary": "Structural audit only; no claim entailment or source-quality verification.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not issues else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "read":
            return _read(args.topic, args.lang)
        if args.command == "languages":
            return _languages(args.topic, args.lang)
        if args.command == "compile":
            return _compile(args)
        if args.command == "absorb-theory":
            return _absorb_theory(args)
        if args.command == "audit":
            return _audit(args.bundle)
    except (MediaWikiError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"omega-wiki: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
