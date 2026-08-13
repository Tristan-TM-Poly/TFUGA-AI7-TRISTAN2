"""Evidence-bound findings for every open PR LLMT packet.

This compiler combines three already-qualified views without creating a new
memory substrate:
- PRWorkPacket: historical ranking, lineage and M- context;
- TargetFileGraph: exact current changed-file overlap between open PRs;
- InspectionOverlay: exact head/files/static AST evidence for selected history.

Findings are triage evidence only. File overlap is not a merge conflict, static
symbols are not behavioral equivalence, and a high priority score is not a
quality judgment.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
import argparse
import json

from .github_memory import _stable_digest

FINDINGS_SCHEMA_VERSION = "0.2.0"


@dataclass(frozen=True)
class PRFinding:
    finding_type: str
    priority: int
    action: str
    evidence: tuple[str, ...]
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _target_overlap_rows(filegraph: Mapping[str, Any], target_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for edge in filegraph.get("overlap_edges", []):
        left = str(edge.get("left", ""))
        right = str(edge.get("right", ""))
        if target_ref not in {left, right}:
            continue
        neighbor = right if left == target_ref else left
        rows.append(
            {
                "neighbor": neighbor,
                "shared_file_count": int(edge.get("shared_file_count", 0)),
                "shared_files": tuple(str(path) for path in edge.get("shared_files", [])),
            }
        )
    rows.sort(key=lambda row: (-row["shared_file_count"], row["neighbor"]))
    return rows


def _reconstruction_roles(
    filegraph: Mapping[str, Any], target_ref: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    as_reconstruction: list[dict[str, Any]] = []
    as_source: list[dict[str, Any]] = []
    for pair in filegraph.get("reconstruction_pairs", []):
        row = dict(pair)
        if str(pair.get("reconstruction_ref", "")) == target_ref:
            as_reconstruction.append(row)
        if str(pair.get("source_ref", "")) == target_ref:
            as_source.append(row)
    as_reconstruction.sort(key=lambda row: (-int(row.get("shared_file_count", 0)), str(row.get("source_ref", ""))))
    as_source.sort(key=lambda row: (-int(row.get("shared_file_count", 0)), str(row.get("reconstruction_ref", ""))))
    return as_reconstruction, as_source


def _inspected_reuse_rows(overlay: Mapping[str, Any], target_ref: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in overlay.get("overlays", []):
        affected = {str(ref) for ref in item.get("affected_targets", [])}
        if target_ref not in affected:
            continue
        rows.append(
            {
                "ref": str(item.get("ref", "")),
                "inspection_state": str(item.get("inspection_state", "")),
                "head_sha": item.get("head_sha"),
                "changed_file_count": len(item.get("changed_files", [])),
                "symbol_count": len(item.get("symbol_assets", [])),
                "fanout": int(item.get("fanout", 0)),
                "best_historical_rank": item.get("best_historical_rank"),
                "errors": tuple(str(error) for error in item.get("errors", [])),
            }
        )
    rows.sort(
        key=lambda row: (
            row["inspection_state"] != "HYDRATED_STATIC_AST",
            row["best_historical_rank"] if row["best_historical_rank"] is not None else 10**9,
            -row["fanout"],
            row["ref"],
        )
    )
    return rows


def _negative_memory(packet: Mapping[str, Any]) -> tuple[str, ...]:
    rows: list[str] = []
    for line in packet.get("target", {}).get("failure_memory", []):
        text = str(line).strip()
        if text:
            rows.append(f"target:{text}")
    for candidate in packet.get("historical_retrieval", {}).get("candidates", []):
        ref = str(candidate.get("ref", ""))
        for line in candidate.get("failure_memory", []):
            text = str(line).strip()
            if text:
                rows.append(f"{ref}:{text}")
    return tuple(dict.fromkeys(rows))


def compile_pr_findings(
    portfolio: Mapping[str, Any],
    filegraph: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    if portfolio.get("schema") != "omega-pr-llmt-portfolio/v0.1.0":
        raise ValueError(f"unsupported portfolio schema: {portfolio.get('schema')}")
    if filegraph.get("schema") != "omega-pr-llmt-target-filegraph/v0.2.0":
        raise ValueError(f"unsupported filegraph schema: {filegraph.get('schema')}")
    if overlay.get("schema") != "omega-pr-llmt-inspection-overlay/v0.1.0":
        raise ValueError(f"unsupported inspection overlay schema: {overlay.get('schema')}")
    fingerprint = portfolio.get("fingerprint")
    if filegraph.get("portfolio_fingerprint") != fingerprint:
        raise ValueError("filegraph portfolio fingerprint mismatch")
    if overlay.get("portfolio_fingerprint") != fingerprint:
        raise ValueError("inspection overlay portfolio fingerprint mismatch")

    large_targets = set(filegraph.get("changed_file_distribution", {}).get("large_change_candidates", []))
    target_file_rows = {
        str(row.get("ref", "")): row
        for row in filegraph.get("targets", [])
    }

    packet_rows: list[dict[str, Any]] = []
    aggregate_counts: dict[str, int] = {}

    for packet in portfolio.get("packets", []):
        target = packet.get("target", {})
        target_ref = str(target.get("ref", ""))
        overlaps = _target_overlap_rows(filegraph, target_ref)
        reconstruction_as_target, reconstruction_as_source = _reconstruction_roles(filegraph, target_ref)
        reconstruction_neighbors = {
            str(row.get("source_ref", "")) for row in reconstruction_as_target
        } | {
            str(row.get("reconstruction_ref", "")) for row in reconstruction_as_source
        }
        generic_overlaps = [row for row in overlaps if row["neighbor"] not in reconstruction_neighbors]
        inspected = _inspected_reuse_rows(overlay, target_ref)
        negatives = _negative_memory(packet)
        prior_lineage = tuple(packet.get("declared_prior_lineage", []))
        descendants = tuple(packet.get("known_later_descendants", []))
        target_files = target_file_rows.get(target_ref, {})

        findings: list[PRFinding] = []

        if reconstruction_as_target:
            findings.append(
                PRFinding(
                    finding_type="DECLARED_RECONSTRUCTION_PAIR",
                    priority=5,
                    action=(
                        "Review this reconstruction against its declared source as a replacement/supersession candidate; "
                        "compare exact blobs, tests and current-base behavior before any close/merge decision."
                    ),
                    evidence=tuple(
                        f"source={row.get('source_ref')};shared_files={row.get('shared_file_count')};"
                        f"same_changed_file_set={row.get('same_changed_file_set')};evidence={row.get('evidence')}"
                        for row in reconstruction_as_target[:4]
                    ),
                    boundary=(
                        "Declared reconstruction plus changed-path agreement is strong provenance evidence, but it does not prove byte identity, "
                        "correctness, merge readiness, or authorization to supersede/close the source PR."
                    ),
                )
            )

        if reconstruction_as_source:
            findings.append(
                PRFinding(
                    finding_type="DECLARED_RECONSTRUCTION_SOURCE",
                    priority=5,
                    action=(
                        "Inspect the newer declared reconstruction before editing this source PR; prefer one canonical repair locus and preserve this PR as provenance until replacement is verified."
                    ),
                    evidence=tuple(
                        f"reconstruction={row.get('reconstruction_ref')};shared_files={row.get('shared_file_count')};"
                        f"same_changed_file_set={row.get('same_changed_file_set')};evidence={row.get('evidence')}"
                        for row in reconstruction_as_source[:4]
                    ),
                    boundary=(
                        "A declared reconstruction is a supersession-review signal, not an automatic supersession, closure, merge, or deletion instruction."
                    ),
                )
            )

        if generic_overlaps:
            max_shared = max(row["shared_file_count"] for row in generic_overlaps)
            priority = 4 if max_shared >= 5 else 3 if max_shared >= 2 else 2
            evidence = tuple(
                f"{row['neighbor']}:{row['shared_file_count']} shared file(s)"
                for row in generic_overlaps[:5]
            )
            findings.append(
                PRFinding(
                    finding_type="FILE_OVERLAP_REVIEW",
                    priority=priority,
                    action="Inspect the strongest exact-file overlap neighbors before editing shared surfaces.",
                    evidence=evidence,
                    boundary="Exact changed-file overlap is a review queue; it does not prove merge conflict, duplicate intent, or semantic convergence.",
                )
            )

        if target_ref in large_targets:
            findings.append(
                PRFinding(
                    finding_type="LARGE_CHANGE_SURFACE",
                    priority=2,
                    action="Prefer staged review and targeted tests because this PR is in the current-corpus p90 changed-file surface.",
                    evidence=(f"changed_file_count={int(target_files.get('changed_file_count', 0))}",),
                    boundary="Large change surface is an inspection-cost signal, not a quality or correctness judgment.",
                )
            )

        successful_inspected = [row for row in inspected if row["inspection_state"] == "HYDRATED_STATIC_AST"]
        if successful_inspected:
            evidence = tuple(
                f"{row['ref']}@{row['head_sha']}:files={row['changed_file_count']},symbols={row['symbol_count']}"
                for row in successful_inspected[:5]
            )
            findings.append(
                PRFinding(
                    finding_type="INSPECTED_REUSE_CANDIDATE",
                    priority=4,
                    action="Compare the exact inspected implementation/tests before creating overlapping code; reuse, compose or extend only after compatibility checks.",
                    evidence=evidence,
                    boundary="Hydrated source and static AST evidence improve inspection quality but do not prove reusable behavior or compatibility.",
                )
            )
        else:
            findings.append(
                PRFinding(
                    finding_type="DEEP_EVIDENCE_GAP",
                    priority=1,
                    action="Schedule exact historical candidate hydration before making a strong reuse/no-reuse claim.",
                    evidence=(f"ranked_candidates={len(packet.get('historical_retrieval', {}).get('candidates', []))}",),
                    boundary="Missing deep evidence is uncertainty, not evidence that no reusable implementation exists.",
                )
            )

        if prior_lineage:
            findings.append(
                PRFinding(
                    finding_type="DECLARED_PRIOR_LINEAGE",
                    priority=3,
                    action="Verify declared ancestor heads and preserve the dependency/reuse rationale in future changes.",
                    evidence=tuple(
                        f"{row.get('relation')}->{row.get('target_ref')}"
                        for row in prior_lineage[:6]
                    ),
                    boundary="Declared lineage is provenance evidence, not causal dependency or semantic correctness proof.",
                )
            )

        if descendants:
            findings.append(
                PRFinding(
                    finding_type="KNOWN_LATER_DESCENDANT",
                    priority=3,
                    action="Inspect later descendants before modifying this PR so fixes land at the correct layer and are not duplicated downstream.",
                    evidence=tuple(
                        f"{row.get('source_ref')}:{row.get('relation')}"
                        for row in descendants[:6]
                    ),
                    boundary="A later descendant can expose stack/reuse context but does not automatically supersede this PR.",
                )
            )

        if negatives:
            findings.append(
                PRFinding(
                    finding_type="NEGATIVE_MEMORY_AVAILABLE",
                    priority=3,
                    action="Consult the recorded M- evidence before selecting or repeating a historical approach.",
                    evidence=negatives[:6],
                    boundary="Negative memory is context-bound counterevidence; it is not a universal refutation of an approach.",
                )
            )

        findings.sort(key=lambda row: (-row.priority, row.finding_type))
        priority_score = sum(row.priority for row in findings)
        for finding in findings:
            aggregate_counts[finding.finding_type] = aggregate_counts.get(finding.finding_type, 0) + 1

        packet_rows.append(
            {
                "target_ref": target_ref,
                "target_number": target.get("number"),
                "title": target.get("title"),
                "head_sha": target.get("head_sha"),
                "changed_file_count": int(target_files.get("changed_file_count", 0)),
                "file_overlap_neighbor_count": len(overlaps),
                "generic_file_overlap_neighbor_count": len(generic_overlaps),
                "reconstruction_as_target_count": len(reconstruction_as_target),
                "reconstruction_as_source_count": len(reconstruction_as_source),
                "max_shared_file_count": max((row["shared_file_count"] for row in overlaps), default=0),
                "inspected_reuse_candidate_count": len(successful_inspected),
                "declared_prior_lineage_count": len(prior_lineage),
                "known_later_descendant_count": len(descendants),
                "negative_memory_count": len(negatives),
                "priority_score": priority_score,
                "findings": [finding.to_dict() for finding in findings],
            }
        )

    packet_rows.sort(
        key=lambda row: (
            -row["priority_score"],
            -row["max_shared_file_count"],
            -(row["target_number"] or -1),
            row["target_ref"],
        )
    )
    without_deep = sum(
        1 for row in packet_rows if row["inspected_reuse_candidate_count"] == 0
    )
    with_overlap = sum(1 for row in packet_rows if row["file_overlap_neighbor_count"] > 0)
    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-findings/v{FINDINGS_SCHEMA_VERSION}",
        "portfolio_fingerprint": fingerprint,
        "filegraph_fingerprint": filegraph.get("fingerprint"),
        "inspection_overlay_fingerprint": overlay.get("fingerprint"),
        "packet_count": len(packet_rows),
        "finding_counts": dict(sorted(aggregate_counts.items())),
        "packets_with_file_overlap": with_overlap,
        "packets_without_deep_reuse_evidence": without_deep,
        "reconstruction_pair_count": int(filegraph.get("reconstruction_pair_count", 0)),
        "top_priority_targets": [row["target_ref"] for row in packet_rows[:12]],
        "packets": packet_rows,
        "authority": {
            "read": True,
            "draft_analysis": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
        },
        "oak_boundaries": [
            "PRIORITY_SCORE != QUALITY_SCORE",
            "FILE_OVERLAP != MERGE_CONFLICT",
            "STATIC_AST != BEHAVIORAL_EQUIVALENCE",
            "DECLARED_LINEAGE != CAUSAL_DEPENDENCY_PROOF",
            "DECLARED_RECONSTRUCTION != BYTE_IDENTITY",
            "RECONSTRUCTION_PAIR != AUTOMATIC_SUPERSESSION",
            "M_MINUS != UNIVERSAL_REFUTATION",
            "FINDING != AUTHORIZATION_TO_MUTATE",
        ],
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload


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
    parser = argparse.ArgumentParser(prog="omega-pr-llmt-findings")
    parser.add_argument("portfolio")
    parser.add_argument("filegraph")
    parser.add_argument("overlay")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    payload = compile_pr_findings(_load(args.portfolio), _load(args.filegraph), _load(args.overlay))
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
