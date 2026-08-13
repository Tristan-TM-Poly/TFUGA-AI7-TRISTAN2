from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence
import argparse
import base64
import json
import lzma
import os
import re

from .github_memory import GitHubMemoryIndex, GitHubPRSource, PRMemory, _stable_digest, _tokens
from .github_cumulative_intelligence import _CONCEPT_RE, _FAILURE_RE, _LINEAGE_PATTERNS

SEED_SCHEMA_VERSION = "0.1.0"
_SEED_SCHEMA = f"omega-pr-history-seed/v{SEED_SCHEMA_VERSION}"
_MATERIALIZATION_SCHEMA = f"omega-pr-history-seed-materialization/v{SEED_SCHEMA_VERSION}"
_DELTA_SCHEMA = f"omega-pr-history-seed-delta/v{SEED_SCHEMA_VERSION}"


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _failure_lines(body: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in body.splitlines()
        if line.strip() and _FAILURE_RE.search(line)
    )


def _historical_lines(body: str) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for relation, pattern in _LINEAGE_PATTERNS:
        for match in pattern.finditer(body):
            rows.append((relation, match.group(0).strip()))
    return tuple(rows)


def _token_triggers_failure(token: str) -> bool:
    return bool(_FAILURE_RE.search(token))


def compress_body_for_retrieval(body: str) -> str:
    """Lossy body compression preserving current retrieval/genome observables.

    The compact body preserves:
    - the exact `_tokens(body)` set used by PR retrieval;
    - exact Ω concept strings used by PRGenomeCompiler;
    - exact failure-memory lines used by #450 as inspection leads;
    - exact R0.8→R1.2 historical-lineage directive lines.

    It is not a source-text archive and must never be treated as one.
    """

    body = str(body or "")
    original_failures = _failure_lines(body)
    original_history = _historical_lines(body)
    body_tokens = list(_tokens(body))

    # Tokens that would become synthetic failure-memory lines if written bare
    # are encoded with `_x`. `_tokens` splits `_` and discards one-letter `x`,
    # preserving the token while keeping _FAILURE_RE from matching the bag line.
    encoded_tokens = [
        f"{token}_x" if _token_triggers_failure(token) else token
        for token in body_tokens
    ]

    lines: list[str] = []
    if encoded_tokens:
        lines.append(" ".join(encoded_tokens))

    for concept in sorted(set(_CONCEPT_RE.findall(body))):
        if _FAILURE_RE.search(concept):
            if not any(concept in line for line in original_failures):
                raise ValueError(
                    "cannot preserve concept without synthesizing failure-memory line: "
                    f"{concept}"
                )
            continue
        lines.append(concept)

    lines.extend(original_failures)
    lines.extend(line for _, line in original_history)
    return "\n".join(dict.fromkeys(line for line in lines if line))


def compile_retrieval_seed_payload(
    full_index_payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compile a retrieval-equivalent CVCD seed from a full GitHubMemoryIndex payload."""

    # Normalize first so the comparison is against the canonical runtime shape.
    original = GitHubMemoryIndex.from_dict(full_index_payload).to_dict()
    compact = json.loads(json.dumps(original, ensure_ascii=False))
    compact.pop("fingerprint", None)

    keyword_equivalent = 0
    concept_equivalent = 0
    failure_equivalent = 0
    historical_line_equivalent = 0

    original_prs = {f"pr:{row['repository']}#{row['number']}": row for row in original["prs"]}
    for row in compact["prs"]:
        ref = f"pr:{row['repository']}#{row['number']}"
        source = original_prs[ref]
        source_body = str(source.get("body") or "")
        row["body"] = compress_body_for_retrieval(source_body)

        source_keywords = _tokens(
            (
                str(source.get("title") or ""),
                source_body,
                *map(str, source.get("files", [])),
            )
        )
        compact_keywords = _tokens(
            (
                str(row.get("title") or ""),
                str(row.get("body") or ""),
                *map(str, row.get("files", [])),
            )
        )
        if source_keywords != compact_keywords:
            raise ValueError(f"retrieval keyword mismatch after CVCD compression: {ref}")
        keyword_equivalent += 1

        source_concepts = set(
            _CONCEPT_RE.findall(f"{source.get('title', '')}\n{source_body}")
        )
        compact_concepts = set(
            _CONCEPT_RE.findall(f"{row.get('title', '')}\n{row.get('body', '')}")
        )
        if source_concepts != compact_concepts:
            raise ValueError(f"concept mismatch after CVCD compression: {ref}")
        concept_equivalent += 1

        if _failure_lines(source_body) != _failure_lines(str(row.get("body") or "")):
            raise ValueError(f"failure-memory line mismatch after CVCD compression: {ref}")
        failure_equivalent += 1

        if _historical_lines(source_body) != _historical_lines(str(row.get("body") or "")):
            raise ValueError(f"historical-lineage mismatch after CVCD compression: {ref}")
        historical_line_equivalent += 1

    pr_count = len(compact["prs"])
    receipt = {
        "schema": "omega-pr-history-seed-cvcd/v0.1.0",
        "pr_count": pr_count,
        "keyword_equivalent_count": keyword_equivalent,
        "concept_equivalent_count": concept_equivalent,
        "failure_memory_equivalent_count": failure_equivalent,
        "historical_line_equivalent_count": historical_line_equivalent,
        "all_current_retrieval_observables_preserved": all(
            value == pr_count
            for value in (
                keyword_equivalent,
                concept_equivalent,
                failure_equivalent,
                historical_line_equivalent,
            )
        ),
        "source_text_preserved": False,
        "boundary": (
            "CVCD seed preserves the current retrieval/PRGenome observables only. "
            "It is not a verbatim PR-body archive and future algorithms using unseen body semantics must rebuild or version the seed."
        ),
    }
    receipt["fingerprint"] = _stable_digest(receipt)
    return compact, receipt


def encode_seed_payload(payload: Mapping[str, Any]) -> tuple[bytes, bytes, str]:
    raw = json.dumps(
        dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    compressed = lzma.compress(raw, preset=9)
    encoded = base64.b85encode(compressed).decode("ascii")
    return raw, compressed, encoded


@dataclass(frozen=True)
class SeedManifest:
    schema: str
    repository: str
    seed_max_pr_number: int
    source_workflow_run_id: int
    source_artifact_id: int
    source_artifact_sha256: str
    source_head_sha: str
    pr_count: int
    raw_bytes: int
    xz_bytes: int
    base85_chars: int
    raw_sha256: str
    xz_sha256: str
    base85_sha256: str
    cvcd_receipt_fingerprint: str
    shards: tuple[dict[str, Any], ...]
    boundary: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SeedManifest":
        schema = str(payload.get("schema") or "")
        if schema != _SEED_SCHEMA:
            raise ValueError(f"unsupported seed manifest schema: {schema}")
        return cls(
            schema=schema,
            repository=str(payload["repository"]),
            seed_max_pr_number=int(payload["seed_max_pr_number"]),
            source_workflow_run_id=int(payload["source_workflow_run_id"]),
            source_artifact_id=int(payload["source_artifact_id"]),
            source_artifact_sha256=str(payload["source_artifact_sha256"]),
            source_head_sha=str(payload["source_head_sha"]),
            pr_count=int(payload["pr_count"]),
            raw_bytes=int(payload["raw_bytes"]),
            xz_bytes=int(payload["xz_bytes"]),
            base85_chars=int(payload["base85_chars"]),
            raw_sha256=str(payload["raw_sha256"]),
            xz_sha256=str(payload["xz_sha256"]),
            base85_sha256=str(payload["base85_sha256"]),
            cvcd_receipt_fingerprint=str(payload["cvcd_receipt_fingerprint"]),
            shards=tuple(dict(row) for row in payload.get("shards", [])),
            boundary=str(payload.get("boundary") or ""),
        )


def load_seed_manifest(path: str | Path) -> SeedManifest:
    return SeedManifest.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def materialize_seed(
    manifest_path: str | Path,
) -> tuple[GitHubMemoryIndex, dict[str, Any]]:
    manifest_path = Path(manifest_path)
    manifest = load_seed_manifest(manifest_path)
    parts: list[str] = []
    for row in manifest.shards:
        shard_path = manifest_path.parent / str(row["file"])
        text = shard_path.read_text(encoding="ascii").strip()
        if len(text) != int(row["chars"]):
            raise ValueError(f"seed shard length mismatch: {shard_path}")
        if _sha(text.encode("ascii")) != str(row["sha256"]):
            raise ValueError(f"seed shard hash mismatch: {shard_path}")
        parts.append(text)

    encoded = "".join(parts)
    if len(encoded) != manifest.base85_chars:
        raise ValueError("base85 seed length mismatch")
    if _sha(encoded.encode("ascii")) != manifest.base85_sha256:
        raise ValueError("base85 seed hash mismatch")

    compressed = base64.b85decode(encoded.encode("ascii"))
    if len(compressed) != manifest.xz_bytes or _sha(compressed) != manifest.xz_sha256:
        raise ValueError("xz seed integrity mismatch")
    raw = lzma.decompress(compressed)
    if len(raw) != manifest.raw_bytes or _sha(raw) != manifest.raw_sha256:
        raise ValueError("raw seed integrity mismatch")

    payload = json.loads(raw.decode("utf-8"))
    index = GitHubMemoryIndex.from_dict(payload)
    repo_prs = [pr for pr in index.prs.values() if pr.repository == manifest.repository]
    if len(repo_prs) != manifest.pr_count:
        raise ValueError("seed PR count mismatch")
    if max((pr.number for pr in repo_prs), default=0) != manifest.seed_max_pr_number:
        raise ValueError("seed maximum PR number mismatch")

    normalized = index.to_dict()
    receipt = {
        "schema": _MATERIALIZATION_SCHEMA,
        "repository": manifest.repository,
        "pr_count": len(repo_prs),
        "seed_max_pr_number": manifest.seed_max_pr_number,
        "source_workflow_run_id": manifest.source_workflow_run_id,
        "source_artifact_id": manifest.source_artifact_id,
        "source_artifact_sha256": manifest.source_artifact_sha256,
        "source_head_sha": manifest.source_head_sha,
        "cvcd_receipt_fingerprint": manifest.cvcd_receipt_fingerprint,
        "raw_sha256": manifest.raw_sha256,
        "normalized_index_fingerprint": normalized["fingerprint"],
        "source_text_preserved": False,
        "network_calls": 0,
        "boundary": manifest.boundary,
    }
    receipt["fingerprint"] = _stable_digest(receipt)
    return index, receipt


def _fetch_pr_number(
    source: GitHubPRSource,
    repository: str,
    number: int,
) -> Mapping[str, Any] | None:
    url = f"{source.api_base}/repos/{repository}/pulls/{number}"
    try:
        payload, _headers = source.transport(url, source.token)
    except RuntimeError as exc:
        text = str(exc)
        if "HTTP 404" in text:
            return None
        raise
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"unexpected PR payload type for #{number}")
    return payload


def extend_seed_to_target(
    index: GitHubMemoryIndex,
    *,
    repository: str,
    target_pr_number: int,
    source: GitHubPRSource | None = None,
) -> dict[str, Any]:
    """Increment a frozen prior seed only across the PR-number delta before target.

    GitHub PR numbers share the issue number space, so 404 entries are retained as
    non-PR gaps. A rate-limit/error produces HOLD with the partial index preserved.
    """

    if target_pr_number <= 0:
        raise ValueError("target_pr_number must be positive")
    current_max = max(
        (pr.number for pr in index.prs.values() if pr.repository == repository),
        default=0,
    )
    start = current_max + 1
    stop = target_pr_number
    needed_numbers = tuple(range(start, stop)) if stop > start else ()

    added: list[str] = []
    non_pr_gaps: list[int] = []
    errors: list[dict[str, Any]] = []
    network_calls = 0
    status = "SEED_COMPLETE_FOR_TARGET" if not needed_numbers else "DELTA_PENDING"

    if needed_numbers and source is None:
        status = "HOLD_DELTA_SOURCE_REQUIRED"
    elif source is not None:
        for number in needed_numbers:
            network_calls += 1
            try:
                payload = _fetch_pr_number(source, repository, number)
            except RuntimeError as exc:
                message = str(exc)
                errors.append({"number": number, "error": message})
                if "rate limit" in message.lower() or "HTTP 403" in message:
                    status = "HOLD_RATE_LIMIT"
                else:
                    status = "HOLD_DELTA_ERROR"
                break
            if payload is None:
                non_pr_gaps.append(number)
                continue
            pr = PRMemory.from_github(repository, payload, files=())
            index.add_pr(pr)
            added.append(pr.ref)
        else:
            status = "DELTA_COMPLETE"

    final_max = max(
        (pr.number for pr in index.prs.values() if pr.repository == repository),
        default=0,
    )
    complete_for_target = status in {"SEED_COMPLETE_FOR_TARGET", "DELTA_COMPLETE"}
    receipt = {
        "schema": _DELTA_SCHEMA,
        "repository": repository,
        "target_pr_number": target_pr_number,
        "seed_or_current_max_pr_number": current_max,
        "needed_numbers": list(needed_numbers),
        "added_pr_refs": added,
        "non_pr_gaps": non_pr_gaps,
        "errors": errors,
        "network_calls": network_calls,
        "status": status,
        "complete_for_target": complete_for_target,
        "final_observed_max_pr_number": final_max,
        "boundary": (
            "A frozen seed is a historical retrieval snapshot, not current lifecycle truth. "
            "Delta HOLD forbids claiming complete prior history or physicalizing reuse decisions."
        ),
    }
    receipt["fingerprint"] = _stable_digest(receipt)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize and optionally increment the verified Ω PR history seed."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target-pr", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--extend-live", action="store_true")
    args = parser.parse_args(argv)

    index, seed_receipt = materialize_seed(args.manifest)
    if args.repository != seed_receipt["repository"]:
        raise ValueError("seed repository does not match requested repository")

    source = None
    if args.extend_live:
        source = GitHubPRSource(token=os.environ.get("GITHUB_TOKEN"))
    delta_receipt = extend_seed_to_target(
        index,
        repository=args.repository,
        target_pr_number=args.target_pr,
        source=source,
    )
    output = index.to_dict()
    Path(args.output).write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "schema": "omega-pr-history-seed-run/v0.1.0",
        "seed": seed_receipt,
        "delta": delta_receipt,
        "complete_for_target": bool(delta_receipt["complete_for_target"]),
        "write_authority_granted": False,
        "boundary": (
            "Seed materialization and delta reads are evidence preparation only. "
            "Incomplete delta status must route downstream physicalization to HOLD."
        ),
    }
    receipt["fingerprint"] = _stable_digest(receipt)
    Path(args.receipt).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
