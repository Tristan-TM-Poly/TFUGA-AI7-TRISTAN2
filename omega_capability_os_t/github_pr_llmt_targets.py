"""Current-target file graph for all open PR LLMT packets.

This layer performs lightweight exact hydration of target PR metadata and changed
filenames, without fetching candidate source bodies or executing code. It turns
all open PRs into a conflict/reuse file graph before deeper per-symbol work.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any, Mapping
import argparse
import json
import os
import re

from .github_memory import GitHubMemoryIndex, GitHubPRSource, PRMemory, _stable_digest
from .github_memory_zoom import ProgressiveGitHubRetriever

TARGET_FILEGRAPH_SCHEMA_VERSION = "0.2.0"

_RECONSTRUCTION_PATTERNS = (
    re.compile(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:(?:(?:clean|oak)\s+){0,2}reconstruction\s+of\s+)(.+)$"
    ),
    re.compile(r"(?im)^\s*(?:[-*+]\s*)?reconstructs?\s*:\s*(.+)$"),
)


def _extract_pr_refs(text: str, repository: str) -> tuple[str, ...]:
    refs: list[str] = []
    occupied: set[str] = set()
    for match in re.finditer(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)", text):
        refs.append(f"pr:{match.group(1)}#{int(match.group(2))}")
        occupied.add(match.group(0))
    scrubbed = text
    for token in occupied:
        scrubbed = scrubbed.replace(token, "")
    for number in re.findall(r"(?:PR[- ]?|#)(\d+)", scrubbed, flags=re.IGNORECASE):
        refs.append(f"pr:{repository}#{int(number)}")
    return tuple(dict.fromkeys(refs))


def _declared_reconstruction_refs(pr: PRMemory) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern in _RECONSTRUCTION_PATTERNS:
        for match in pattern.finditer(pr.body or ""):
            evidence = match.group(0).strip()
            for ref in _extract_pr_refs(match.group(1), pr.repository):
                row = (ref, evidence)
                if row in seen:
                    continue
                seen.add(row)
                rows.append(row)
    return tuple(rows)


def compile_target_file_graph(
    index: GitHubMemoryIndex,
    portfolio: Mapping[str, Any],
    source: GitHubPRSource,
    *,
    max_targets: int | None = None,
) -> tuple[dict[str, Any], GitHubMemoryIndex]:
    """Hydrate target changed-file metadata and build exact-path overlap evidence."""
    if portfolio.get("schema") != "omega-pr-llmt-portfolio/v0.1.0":
        raise ValueError(f"unsupported portfolio schema: {portfolio.get('schema')}")
    if max_targets is not None and max_targets < 0:
        raise ValueError("max_targets must be non-negative or omitted")

    target_refs = tuple(
        str(packet["target"]["ref"])
        for packet in portfolio.get("packets", [])
    )
    selected_refs = target_refs if max_targets is None else target_refs[:max_targets]
    retriever = ProgressiveGitHubRetriever(source)
    receipt = retriever.hydrate_refs(
        index,
        selected_refs,
        request_id=f"pr-llmt-target-files:{portfolio.get('fingerprint', 'unknown')}",
        max_files_per_pr=0,
        extract_symbols=False,
    )

    errors_by_ref: dict[str, list[dict[str, str]]] = {}
    for error in receipt.errors:
        errors_by_ref.setdefault(str(error.get("ref", "")), []).append(dict(error))

    targets: list[dict[str, Any]] = []
    file_targets: dict[str, set[str]] = {}
    target_files_by_ref: dict[str, tuple[str, ...]] = {}
    for ref in selected_refs:
        pr = index.prs.get(ref)
        files = tuple(pr.files) if pr else ()
        target_files_by_ref[ref] = files
        for path in files:
            file_targets.setdefault(path, set()).add(ref)
        targets.append(
            {
                "ref": ref,
                "head_sha": pr.head_sha if pr else None,
                "head_ref": pr.head_ref if pr else None,
                "base_ref": pr.base_ref if pr else None,
                "lifecycle": pr.lifecycle if pr else None,
                "title": pr.title if pr else None,
                "changed_file_count": len(files),
                "changed_files": list(files),
                "errors": errors_by_ref.get(ref, []),
            }
        )

    shared_files = [
        {
            "path": path,
            "fanout": len(refs),
            "target_refs": sorted(refs),
        }
        for path, refs in file_targets.items()
        if len(refs) > 1
    ]
    shared_files.sort(key=lambda row: (-row["fanout"], row["path"]))

    pair_files: dict[tuple[str, str], list[str]] = {}
    for row in shared_files:
        for left, right in combinations(row["target_refs"], 2):
            pair_files.setdefault((left, right), []).append(row["path"])
    overlap_edges = [
        {
            "left": left,
            "right": right,
            "shared_file_count": len(paths),
            "shared_files": sorted(paths),
        }
        for (left, right), paths in pair_files.items()
    ]
    overlap_edges.sort(
        key=lambda row: (-row["shared_file_count"], row["left"], row["right"])
    )
    overlap_by_pair = {
        frozenset((row["left"], row["right"])): row
        for row in overlap_edges
    }

    reconstruction_pairs: list[dict[str, Any]] = []
    seen_reconstructions: set[tuple[str, str]] = set()
    selected_ref_set = set(selected_refs)
    for reconstruction_ref in selected_refs:
        pr = index.prs.get(reconstruction_ref)
        if pr is None:
            continue
        for source_ref, evidence in _declared_reconstruction_refs(pr):
            if source_ref not in selected_ref_set or source_ref == reconstruction_ref:
                continue
            overlap = overlap_by_pair.get(frozenset((source_ref, reconstruction_ref)))
            if overlap is None:
                continue
            relation_key = (source_ref, reconstruction_ref)
            if relation_key in seen_reconstructions:
                continue
            seen_reconstructions.add(relation_key)
            source_files = set(target_files_by_ref.get(source_ref, ()))
            reconstruction_files = set(target_files_by_ref.get(reconstruction_ref, ()))
            reconstruction_pairs.append(
                {
                    "source_ref": source_ref,
                    "reconstruction_ref": reconstruction_ref,
                    "evidence": evidence,
                    "shared_file_count": int(overlap["shared_file_count"]),
                    "shared_files": list(overlap["shared_files"]),
                    "source_changed_file_count": len(source_files),
                    "reconstruction_changed_file_count": len(reconstruction_files),
                    "same_changed_file_set": bool(source_files) and source_files == reconstruction_files,
                    "boundary": (
                        "Declared reconstruction plus exact changed-path overlap is strong provenance/review evidence. "
                        "Matching changed-file sets do not prove byte-identical blobs, equivalent commits, correct tests, or safe supersession."
                    ),
                }
            )
    reconstruction_pairs.sort(
        key=lambda row: (
            -row["shared_file_count"],
            row["source_ref"],
            row["reconstruction_ref"],
        )
    )

    file_counts = sorted(row["changed_file_count"] for row in targets)
    if file_counts:
        p90_index = max(0, min(len(file_counts) - 1, (9 * len(file_counts) + 9) // 10 - 1))
        p90 = file_counts[p90_index]
        median = file_counts[len(file_counts) // 2]
    else:
        p90 = 0
        median = 0
    large_change_candidates = [
        row["ref"]
        for row in targets
        if row["changed_file_count"] >= p90 and row["changed_file_count"] > 0
    ]
    targets_with_overlap = {
        ref
        for row in shared_files
        for ref in row["target_refs"]
    }

    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-target-filegraph/v{TARGET_FILEGRAPH_SCHEMA_VERSION}",
        "portfolio_fingerprint": portfolio.get("fingerprint"),
        "operational_budget": {
            "max_targets": max_targets,
            "architecture_hard_cap": False,
            "selected_target_count": len(selected_refs),
            "total_target_count": len(target_refs),
        },
        "hydrated_target_count": len(receipt.hydrated_prs),
        "error_count": len(receipt.errors),
        "total_changed_file_observations": sum(row["changed_file_count"] for row in targets),
        "unique_changed_file_count": len(file_targets),
        "shared_file_count": len(shared_files),
        "overlap_edge_count": len(overlap_edges),
        "targets_with_file_overlap_count": len(targets_with_overlap),
        "targets_with_file_overlap_fraction": round(
            len(targets_with_overlap) / len(selected_refs), 6
        ) if selected_refs else 0.0,
        "reconstruction_pair_count": len(reconstruction_pairs),
        "reconstruction_pairs": reconstruction_pairs,
        "changed_file_distribution": {
            "median": median,
            "p90": p90,
            "large_change_candidate_count": len(large_change_candidates),
            "large_change_candidates": large_change_candidates,
            "boundary": (
                "p90 is a within-corpus inspection priority signal only; a large diff is not an error or low-quality PR."
            ),
        },
        "targets": targets,
        "shared_files": shared_files,
        "overlap_edges": overlap_edges,
        "progressive_retrieval": receipt.to_dict(),
        "authority": {
            "read": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "oak_boundaries": [
            "SAME_FILE != SAME_INTENT",
            "FILE_OVERLAP != MERGE_CONFLICT",
            "LARGE_DIFF != LOW_QUALITY",
            "CHANGED_FILENAME != BEHAVIORAL_EQUIVALENCE",
            "RECONSTRUCTION_DECLARATION != BYTE_IDENTITY",
            "SAME_CHANGED_FILE_SET != SAME_BLOBS",
            "RECONSTRUCTION_PAIR != AUTOMATIC_SUPERSESSION",
            "TARGET_FILEGRAPH != GITHUB_WRITE_AUTHORITY",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload, index


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str | None, payload: Mapping[str, Any]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-pr-llmt-targets")
    parser.add_argument("index")
    parser.add_argument("portfolio")
    parser.add_argument("--max-targets", type=int)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output-index")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    index = GitHubMemoryIndex.from_dict(_load(args.index))
    portfolio = _load(args.portfolio)
    source = GitHubPRSource(token=os.getenv(args.token_env) if args.token_env else None)
    payload, hydrated = compile_target_file_graph(
        index,
        portfolio,
        source,
        max_targets=args.max_targets,
    )
    _write(args.output_index, hydrated.to_dict())
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
