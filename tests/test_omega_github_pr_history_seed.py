from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

from omega_capability_os_t.github_memory import GitHubMemoryIndex, _tokens
from omega_capability_os_t.github_cumulative_intelligence import (
    _CONCEPT_RE,
    _FAILURE_RE,
    _LINEAGE_PATTERNS,
)
from omega_capability_os_t.github_pr_history_seed import (
    compile_retrieval_seed_payload,
    encode_seed_payload,
    extend_seed_to_target,
    materialize_seed,
)


def _index_payload() -> dict:
    return {
        "schema": "omega-github-memory-index/v0.1.0",
        "capabilities": [],
        "prs": [
            {
                "repository": "o/r",
                "number": 10,
                "state": "closed",
                "title": "Ω-SEED-T reuse compiler",
                "body": (
                    "This compiler failed_checks once but later passed.\n"
                    "blocked: token-with-underscore should not synthesize failure memory\n"
                    "stacked on: #8\n"
                    "M- exact negative line\n"
                    "The remaining narrative contains generation residual provenance."
                ),
                "head_sha": "a" * 40,
                "head_ref": "feat/seed",
                "base_ref": "main",
                "draft": False,
                "merged": True,
                "files": ["omega/seed.py", "tests/test_seed.py"],
                "updated_at": "2026-08-01T00:00:00Z",
                "url": "https://example.invalid/pr/10"
            },
            {
                "repository": "o/r",
                "number": 12,
                "state": "open",
                "title": "second historical PR",
                "body": "reconstructs: #10\nplain search words alpha beta gamma",
                "head_sha": "b" * 40,
                "head_ref": "feat/second",
                "base_ref": "main",
                "draft": True,
                "merged": False,
                "files": [],
                "updated_at": "2026-08-02T00:00:00Z",
                "url": "https://example.invalid/pr/12"
            }
        ],
        "assets": [],
        "edges": [],
        "atlas_receipts": []
    }


def _failure_lines(body: str) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in body.splitlines()
        if line.strip() and _FAILURE_RE.search(line)
    )


def _history_lines(body: str) -> tuple[tuple[str, str], ...]:
    rows = []
    for relation, pattern in _LINEAGE_PATTERNS:
        for match in pattern.finditer(body):
            rows.append((relation, match.group(0).strip()))
    return tuple(rows)


def test_cvcd_seed_preserves_current_retrieval_observables():
    original = GitHubMemoryIndex.from_dict(_index_payload()).to_dict()
    compact, receipt = compile_retrieval_seed_payload(original)
    assert receipt["all_current_retrieval_observables_preserved"] is True
    assert receipt["pr_count"] == 2
    assert receipt["source_text_preserved"] is False

    original_by_ref = {
        f"pr:{row['repository']}#{row['number']}": row for row in original["prs"]
    }
    compact_by_ref = {
        f"pr:{row['repository']}#{row['number']}": row for row in compact["prs"]
    }
    for ref, source in original_by_ref.items():
        compressed = compact_by_ref[ref]
        assert _tokens((source["title"], source["body"], *source["files"])) == _tokens(
            (compressed["title"], compressed["body"], *compressed["files"])
        )
        assert set(_CONCEPT_RE.findall(source["title"] + "\n" + source["body"])) == set(
            _CONCEPT_RE.findall(compressed["title"] + "\n" + compressed["body"])
        )
        assert _failure_lines(source["body"]) == _failure_lines(compressed["body"])
        assert _history_lines(source["body"]) == _history_lines(compressed["body"])


def test_seed_manifest_materializes_and_verifies_hashes(tmp_path: Path):
    compact, cvcd = compile_retrieval_seed_payload(_index_payload())
    raw, xz, encoded = encode_seed_payload(compact)
    midpoint = len(encoded) // 2
    parts = [encoded[:midpoint], encoded[midpoint:]]
    shard_rows = []
    for i, text in enumerate(parts, start=1):
        name = f"part_{i:02d}.b85"
        (tmp_path / name).write_text(text, encoding="ascii")
        shard_rows.append({
            "file": name,
            "chars": len(text),
            "sha256": sha256(text.encode("ascii")).hexdigest(),
        })
    manifest = {
        "schema": "omega-pr-history-seed/v0.1.0",
        "repository": "o/r",
        "seed_max_pr_number": 12,
        "source_workflow_run_id": 1,
        "source_artifact_id": 2,
        "source_artifact_sha256": "f" * 64,
        "source_head_sha": "c" * 40,
        "pr_count": 2,
        "raw_bytes": len(raw),
        "xz_bytes": len(xz),
        "base85_chars": len(encoded),
        "raw_sha256": sha256(raw).hexdigest(),
        "xz_sha256": sha256(xz).hexdigest(),
        "base85_sha256": sha256(encoded.encode("ascii")).hexdigest(),
        "cvcd_receipt_fingerprint": cvcd["fingerprint"],
        "shards": shard_rows,
        "boundary": "test seed",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    index, receipt = materialize_seed(manifest_path)
    assert len(index.prs) == 2
    assert receipt["network_calls"] == 0
    assert receipt["pr_count"] == 2
    assert receipt["seed_max_pr_number"] == 12

    # Tampering must fail before JSON interpretation.
    (tmp_path / "part_01.b85").write_text(parts[0] + "x", encoding="ascii")
    try:
        materialize_seed(manifest_path)
    except ValueError as exc:
        assert "length mismatch" in str(exc) or "hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered seed shard must fail")


class _FakeSource:
    api_base = "https://api.github.invalid"
    token = None

    def __init__(self, payloads=None, fail=None):
        self.payloads = payloads or {}
        self.fail = fail
        self.calls = []

    def transport(self, url, token):
        self.calls.append(url)
        number = int(url.rsplit("/", 1)[-1])
        if self.fail and number == self.fail:
            raise RuntimeError("GitHub API HTTP 403: rate limit exceeded for installation")
        if number not in self.payloads:
            raise RuntimeError("GitHub API HTTP 404: not found")
        return self.payloads[number], {}


def _new_pr(number: int) -> dict:
    return {
        "number": number,
        "state": "closed",
        "title": f"PR {number}",
        "body": "delta history",
        "draft": False,
        "merged": True,
        "head": {"sha": str(number) * 40, "ref": f"feat/{number}"},
        "base": {"ref": "main"},
        "updated_at": "2026-08-03T00:00:00Z",
        "html_url": f"https://example.invalid/pr/{number}",
    }


def test_target_immediately_after_seed_needs_zero_network_calls():
    index = GitHubMemoryIndex.from_dict(_index_payload())
    receipt = extend_seed_to_target(
        index, repository="o/r", target_pr_number=13, source=None
    )
    assert receipt["status"] == "SEED_COMPLETE_FOR_TARGET"
    assert receipt["complete_for_target"] is True
    assert receipt["network_calls"] == 0


def test_incremental_delta_fetches_only_numbers_after_seed_and_skips_issue_gaps():
    index = GitHubMemoryIndex.from_dict(_index_payload())
    source = _FakeSource(payloads={13: _new_pr(13), 15: _new_pr(15)})
    receipt = extend_seed_to_target(
        index, repository="o/r", target_pr_number=16, source=source
    )
    assert receipt["needed_numbers"] == [13, 14, 15]
    assert receipt["network_calls"] == 3
    assert receipt["added_pr_refs"] == ["pr:o/r#13", "pr:o/r#15"]
    assert receipt["non_pr_gaps"] == [14]
    assert receipt["status"] == "DELTA_COMPLETE"
    assert receipt["complete_for_target"] is True


def test_rate_limit_becomes_hold_with_partial_index_not_false_complete():
    index = GitHubMemoryIndex.from_dict(_index_payload())
    source = _FakeSource(payloads={13: _new_pr(13)}, fail=14)
    receipt = extend_seed_to_target(
        index, repository="o/r", target_pr_number=16, source=source
    )
    assert receipt["added_pr_refs"] == ["pr:o/r#13"]
    assert receipt["status"] == "HOLD_RATE_LIMIT"
    assert receipt["complete_for_target"] is False
    assert receipt["errors"]
