from __future__ import annotations

from dataclasses import asdict
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    CollisionRecord,
    IdentityRecord,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    UnionFind,
    all_pairs,
    build_identity_record,
    file_receipt,
    load_identity_decisions,
    read_jsonl,
    stable_digest,
    title_tokens,
    token_jaccard,
    union_respects_splits,
    write_jsonl,
)


def _canonical_record_id(members: Sequence[IdentityRecord], preferred: Sequence[str]) -> str:
    preferred_set = set(preferred)
    pool = [item for item in members if item.record_id in preferred_set] or list(members)
    return sorted(
        pool,
        key=lambda item: (
            item.source_verified_at is None,
            item.statement_fingerprint is None,
            item.source_id,
            item.source_problem_id,
            item.record_id,
        ),
    )[0].record_id


def _edge(edge: dict[str, Any]) -> dict[str, Any]:
    edge["edge_digest"] = stable_digest(edge)
    return edge


def _write_graphml(
    path: Path,
    records: Sequence[IdentityRecord],
    canonical_rows: Sequence[Mapping[str, Any]],
    merge_edges: Sequence[Mapping[str, Any]],
    alias_edges: Sequence[Mapping[str, Any]],
    candidate_edges: Sequence[Mapping[str, Any]],
) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="kind" for="node" attr.name="kind" attr.type="string"/>',
        '<key id="label" for="node" attr.name="label" attr.type="string"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<graph id="omega-problem-identity-r05" edgedefault="undirected">',
    ]
    for record in records:
        lines.append(
            f'<node id="{escape(record.record_id)}"><data key="kind">source_record</data>'
            f'<data key="label">{escape(record.title)}</data></node>'
        )
    for row in canonical_rows:
        canonical_id = str(row["canonical_problem_id"])
        lines.append(
            f'<node id="{escape(canonical_id)}"><data key="kind">canonical_problem</data>'
            f'<data key="label">{escape(str(row["titles"][0]))}</data></node>'
        )
        for member_id in row["member_record_ids"]:
            lines.append(
                f'<edge source="{escape(str(member_id))}" target="{escape(canonical_id)}">'
                '<data key="relation">member_of</data></edge>'
            )
    for row in merge_edges:
        lines.append(
            f'<edge source="{escape(str(row["left_record_id"]))}" '
            f'target="{escape(str(row["right_record_id"]))}">'
            f'<data key="relation">{escape(str(row["merge_basis"]))}</data></edge>'
        )
    for row in alias_edges:
        lines.append(
            f'<edge source="{escape(str(row["record_id"]))}" '
            f'target="{escape(str(row["canonical_problem_id"]))}">'
            f'<data key="relation">{escape(str(row["alias_basis"]))}</data></edge>'
        )
    for row in candidate_edges:
        lines.append(
            f'<edge source="{escape(str(row["left_record_id"]))}" '
            f'target="{escape(str(row["right_record_id"]))}">'
            '<data key="relation">possible_alias_review</data></edge>'
        )
    lines.extend(["</graph>", "</graphml>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_identity_graph(
    import_paths: Sequence[str | Path],
    output_dir: str | Path,
    *,
    decision_paths: Sequence[str | Path] = (),
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for path in sorted((Path(item) for item in import_paths), key=str):
        rows.extend(read_jsonl(path))
    records = tuple(sorted((build_identity_record(row) for row in rows), key=lambda item: item.record_id))
    if len({record.record_id for record in records}) != len(records):
        raise ValueError("duplicate record_id")
    by_id = {record.record_id: record for record in records}

    decisions = load_identity_decisions(decision_paths)
    for decision in decisions:
        missing = sorted(set(decision.record_ids) - set(by_id))
        if missing:
            raise ValueError(f"{decision.decision_id}: unknown record_ids {missing}")

    split_pairs: set[tuple[str, str]] = set()
    manual_merge_pairs: set[tuple[str, str]] = set()
    alias_pairs: set[tuple[str, str]] = set()
    preferred_canonical: list[str] = []
    for decision in decisions:
        pairs = all_pairs(decision.record_ids)
        if decision.action == "split":
            split_pairs.update(pairs)
        elif decision.action == "merge":
            manual_merge_pairs.update(pairs)
            if decision.canonical_record_id:
                preferred_canonical.append(decision.canonical_record_id)
        else:
            alias_pairs.update(pairs)
    if split_pairs & manual_merge_pairs:
        raise ValueError("direct manual merge/split conflict")

    uf = UnionFind(by_id)
    all_record_ids = tuple(by_id)
    merge_edges: list[dict[str, Any]] = []

    for left, right in sorted(manual_merge_pairs):
        if not union_respects_splits(uf, left, right, split_pairs, all_record_ids):
            raise ValueError(f"manual merge transitively violates split decision: {left}, {right}")
        uf.union(left, right)
        merge_edges.append(_edge({
            "edge_id": f"merge::manual::{stable_digest((left, right))[:16]}",
            "left_record_id": left,
            "right_record_id": right,
            "relation": "same_problem",
            "merge_basis": "manual_evidence_receipt",
            "automatic": False,
        }))

    statement_groups: dict[tuple[Any, ...], list[str]] = {}
    for record in records:
        if record.statement_fingerprint:
            key = (
                record.statement_fingerprint,
                record.front,
                record.quantifier_signature,
                record.domain_signature,
            )
            statement_groups.setdefault(key, []).append(record.record_id)
    for member_ids in statement_groups.values():
        for left, right in sorted(all_pairs(sorted(member_ids))):
            if not union_respects_splits(uf, left, right, split_pairs, all_record_ids):
                continue
            uf.union(left, right)
            merge_edges.append(_edge({
                "edge_id": f"merge::exact_statement::{stable_digest((left, right))[:16]}",
                "left_record_id": left,
                "right_record_id": right,
                "relation": "same_problem",
                "merge_basis": "exact_statement_front_and_signature",
                "automatic": True,
            }))

    collision_rows: list[CollisionRecord] = []
    title_groups: dict[str, list[IdentityRecord]] = {}
    for record in records:
        title_groups.setdefault(record.title_key, []).append(record)
    for title_key, members in sorted(title_groups.items()):
        if len(members) < 2 or len({uf.find(item.record_id) for item in members}) == 1:
            continue
        fingerprints = {item.statement_fingerprint for item in members}
        fronts = {item.front for item in members}
        reasons = ["title_equality_is_not_identity"]
        if None in fingerprints:
            reasons.append("missing_statement")
        if len(fingerprints) > 1:
            reasons.append("different_statement_fingerprints")
        if len(fronts) > 1:
            reasons.append("different_fronts")
        base = {
            "collision_id": f"collision::title::{stable_digest((title_key, sorted(item.record_id for item in members)))[:16]}",
            "collision_type": "same_title_distinct_identity",
            "record_ids": tuple(sorted(item.record_id for item in members)),
            "title_key": title_key,
            "reason_codes": tuple(sorted(reasons)),
            "review_required": True,
        }
        collision_rows.append(CollisionRecord(**base, collision_digest=stable_digest(base)))

    source_key_groups: dict[tuple[str, str], list[IdentityRecord]] = {}
    for record in records:
        source_key_groups.setdefault((record.source_id, record.source_problem_id), []).append(record)
    for key, members in sorted(source_key_groups.items()):
        if len(members) < 2 or len({uf.find(item.record_id) for item in members}) == 1:
            continue
        base = {
            "collision_id": f"collision::source_key::{stable_digest((key, sorted(item.record_id for item in members)))[:16]}",
            "collision_type": "source_identifier_collision",
            "record_ids": tuple(sorted(item.record_id for item in members)),
            "title_key": None,
            "reason_codes": ("same_source_identifier_distinct_identity",),
            "review_required": True,
        }
        collision_rows.append(CollisionRecord(**base, collision_digest=stable_digest(base)))

    groups: dict[str, list[IdentityRecord]] = {}
    for record in records:
        groups.setdefault(uf.find(record.record_id), []).append(record)

    canonical_rows: list[dict[str, Any]] = []
    record_to_canonical: dict[str, str] = {}
    for members in groups.values():
        members = sorted(members, key=lambda item: item.record_id)
        canonical_id = f"problem::{stable_digest(sorted(item.record_id for item in members))[:24]}"
        row = {
            "canonical_problem_id": canonical_id,
            "canonical_record_id": _canonical_record_id(members, preferred_canonical),
            "member_record_ids": [item.record_id for item in members],
            "titles": sorted({item.title for item in members}),
            "alias_keys": sorted({alias for item in members for alias in item.alias_keys + (item.title_key,) if alias}),
            "fronts": sorted({item.front for item in members}),
            "statement_fingerprints": sorted({item.statement_fingerprint for item in members if item.statement_fingerprint}),
            "identity_status": "merged" if len(members) > 1 else "singleton",
            "member_count": len(members),
            "proof_claimed": False,
            "solution_claimed": False,
        }
        row["canonical_digest"] = stable_digest(row)
        canonical_rows.append(row)
        for member in members:
            record_to_canonical[member.record_id] = canonical_id

    alias_edges: list[dict[str, Any]] = []
    for record in records:
        for alias_key in record.alias_keys:
            alias_edges.append(_edge({
                "edge_id": f"alias::declared::{stable_digest((record.record_id, alias_key))[:16]}",
                "record_id": record.record_id,
                "canonical_problem_id": record_to_canonical[record.record_id],
                "alias_key": alias_key,
                "alias_basis": "declared_source_alias",
                "identity_merge": False,
            }))
    for left, right in sorted(alias_pairs):
        for record_id, alias_record_id in ((left, right), (right, left)):
            alias_edges.append(_edge({
                "edge_id": f"alias::manual::{stable_digest((record_id, alias_record_id))[:16]}",
                "record_id": record_id,
                "canonical_problem_id": record_to_canonical[record_id],
                "alias_key": by_id[alias_record_id].title_key,
                "alias_basis": "manual_alias_receipt",
                "identity_merge": False,
            }))

    token_index: dict[str, list[str]] = {}
    title_token_map = {record.record_id: title_tokens(record.title_key) for record in records}
    for record_id, tokens in title_token_map.items():
        for token in tokens:
            token_index.setdefault(token, []).append(record_id)
    candidate_pairs: set[tuple[str, str]] = set()
    for member_ids in token_index.values():
        candidate_pairs.update(all_pairs(sorted(set(member_ids))))
    candidate_edges: list[dict[str, Any]] = []
    for left, right in sorted(candidate_pairs):
        if uf.find(left) == uf.find(right) or by_id[left].front != by_id[right].front:
            continue
        similarity = token_jaccard(title_token_map[left], title_token_map[right])
        if similarity < 0.6:
            continue
        candidate_edges.append(_edge({
            "edge_id": f"candidate::title_tokens::{stable_digest((left, right))[:16]}",
            "left_record_id": left,
            "right_record_id": right,
            "relation": "possible_alias_review",
            "candidate_basis": "distinctive_title_token_jaccard",
            "similarity": round(similarity, 6),
            "identity_merge": False,
            "requires_review": True,
        }))

    source_rows = [asdict(record) for record in records]
    decision_rows = [asdict(decision) for decision in decisions]
    collision_dicts = [asdict(item) for item in sorted(collision_rows, key=lambda item: item.collision_id)]
    canonical_rows.sort(key=lambda row: row["canonical_problem_id"])
    merge_edges.sort(key=lambda row: row["edge_id"])
    alias_edges.sort(key=lambda row: row["edge_id"])
    candidate_edges.sort(key=lambda row: row["edge_id"])

    write_jsonl(output / "source_records.jsonl", source_rows)
    write_jsonl(output / "canonical_problems.jsonl", canonical_rows)
    write_jsonl(output / "identity_edges.jsonl", merge_edges)
    write_jsonl(output / "alias_edges.jsonl", alias_edges)
    write_jsonl(output / "candidate_edges.jsonl", candidate_edges)
    write_jsonl(output / "decision_receipts.jsonl", decision_rows)
    write_jsonl(output / "collision_quarantine.jsonl", collision_dicts)
    _write_graphml(output / "identity_graph.graphml", records, canonical_rows, merge_edges, alias_edges, candidate_edges)

    artifact_names = (
        "source_records.jsonl", "canonical_problems.jsonl", "identity_edges.jsonl",
        "alias_edges.jsonl", "candidate_edges.jsonl", "decision_receipts.jsonl",
        "collision_quarantine.jsonl", "identity_graph.graphml",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifacts": [file_receipt(output / name) for name in artifact_names],
        "fuzzy_merge_allowed": False,
        "title_only_merge_allowed": False,
        "permanent_total_cap": None,
        "solution_claimed": False,
        "formal_proof_claimed": False,
    }
    manifest["digest"] = stable_digest({key: value for key, value in manifest.items() if key != "digest"})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    report = {
        "schema": REPORT_SCHEMA,
        "status": "CERTIFIED_IDENTITY_GRAPH_FIXTURE_R0_5",
        "source_record_count": len(records),
        "canonical_problem_count": len(canonical_rows),
        "automatic_exact_statement_merge_edge_count": sum(row["merge_basis"] == "exact_statement_front_and_signature" for row in merge_edges),
        "manual_merge_edge_count": sum(row["merge_basis"] == "manual_evidence_receipt" for row in merge_edges),
        "alias_edge_count": len(alias_edges),
        "fuzzy_candidate_count": len(candidate_edges),
        "decision_receipt_count": len(decisions),
        "collision_quarantine_count": len(collision_dicts),
        "singleton_count": sum(row["identity_status"] == "singleton" for row in canonical_rows),
        "merged_problem_count": sum(row["identity_status"] == "merged" for row in canonical_rows),
        "fuzzy_merge_count": 0,
        "title_only_merge_count": 0,
        "solution_claimed": False,
        "formal_proof_claimed": False,
        "scientific_validation_claimed": False,
        "permanent_total_cap": None,
        "manifest_digest": manifest["digest"],
    }
    report["digest"] = stable_digest({key: value for key, value in report.items() if key != "digest"})
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
