"""Exact structural measurements for PR-LLMT reconstruction evidence.

This module resolves one narrow, observable part of reconstruction review:
whether the changed files declared by a reconstruction point to identical Git
blob SHA values at the exact source and reconstruction heads.

It never executes candidate code. Blob equality does not prove test success,
behavioral equivalence, base freshness, merge readiness, or safe supersession.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from urllib.parse import quote, urlencode
import argparse
import json
import os

from .github_memory import GitHubPRSource, _stable_digest

STRUCTURAL_MEASUREMENT_SCHEMA_VERSION = "0.1.0"


def _repository_from_pr_ref(ref: str) -> str:
    if not ref.startswith("pr:") or "#" not in ref:
        raise ValueError(f"invalid PR reference: {ref}")
    repository, number = ref[3:].rsplit("#", 1)
    if "/" not in repository or not number.isdigit():
        raise ValueError(f"invalid PR reference: {ref}")
    return repository


def _blob_metadata(
    source: GitHubPRSource,
    repository: str,
    path: str,
    head_sha: str,
) -> dict[str, Any]:
    owner, name = repository.split("/", 1)
    safe_path = quote(path, safe="/")
    url = (
        f"{source.api_base}/repos/{owner}/{name}/contents/{safe_path}?"
        f"{urlencode({'ref': head_sha})}"
    )
    payload = source.transport(url)
    if not isinstance(payload, Mapping):
        raise TypeError(f"expected GitHub contents mapping for {repository}:{path}@{head_sha}")
    if payload.get("type") not in {None, "file"}:
        raise TypeError(f"expected file content for {repository}:{path}@{head_sha}")
    blob_sha = str(payload.get("sha") or "")
    if len(blob_sha) != 40:
        raise ValueError(f"missing/invalid Git blob SHA for {repository}:{path}@{head_sha}")
    return {
        "blob_sha": blob_sha,
        "size": int(payload.get("size", 0) or 0),
        "api_url": str(payload.get("url") or url),
    }


def compile_reconstruction_blob_measurements(
    filegraph: Mapping[str, Any],
    requests: Mapping[str, Any],
    source: GitHubPRSource,
) -> dict[str, Any]:
    if filegraph.get("schema") != "omega-pr-llmt-target-filegraph/v0.2.0":
        raise ValueError(f"unsupported filegraph schema: {filegraph.get('schema')}")
    if requests.get("schema") != "omega-pr-llmt-measurement-requests/v0.1.0":
        raise ValueError(f"unsupported request schema: {requests.get('schema')}")

    targets = {
        str(row.get("ref") or ""): dict(row)
        for row in filegraph.get("targets", [])
        if str(row.get("ref") or "")
    }
    reconstruction_requests: dict[str, list[str]] = {}
    for row in requests.get("requests", []):
        if str(row.get("measurement_kind") or "") != "reconstruction_equivalence_test":
            continue
        target_ref = str(row.get("target_ref") or "")
        request_id = str(row.get("request_id") or "")
        if target_ref and request_id:
            reconstruction_requests.setdefault(target_ref, []).append(request_id)

    measurements: list[dict[str, Any]] = []
    total_compared_files = 0
    total_blob_matches = 0
    total_blob_mismatches = 0
    total_errors = 0

    for pair in filegraph.get("reconstruction_pairs", []):
        source_ref = str(pair.get("source_ref") or "")
        reconstruction_ref = str(pair.get("reconstruction_ref") or "")
        source_target = targets.get(source_ref, {})
        reconstruction_target = targets.get(reconstruction_ref, {})
        source_head = str(source_target.get("head_sha") or "")
        reconstruction_head = str(reconstruction_target.get("head_sha") or "")
        shared_files = tuple(sorted(dict.fromkeys(str(path) for path in pair.get("shared_files", []) if str(path))))
        associated_request_ids = sorted(
            set(reconstruction_requests.get(source_ref, ()))
            | set(reconstruction_requests.get(reconstruction_ref, ()))
        )

        file_results: list[dict[str, Any]] = []
        pair_errors: list[dict[str, str]] = []
        mismatch_count = 0
        match_count = 0

        if not source_head or not reconstruction_head:
            pair_errors.append(
                {
                    "path": "",
                    "error": "missing exact source or reconstruction head SHA in target filegraph",
                }
            )
        else:
            source_repository = _repository_from_pr_ref(source_ref)
            reconstruction_repository = _repository_from_pr_ref(reconstruction_ref)
            for path in shared_files:
                try:
                    left = _blob_metadata(source, source_repository, path, source_head)
                    right = _blob_metadata(source, reconstruction_repository, path, reconstruction_head)
                    equal = left["blob_sha"] == right["blob_sha"]
                    match_count += int(equal)
                    mismatch_count += int(not equal)
                    file_results.append(
                        {
                            "path": path,
                            "source_blob_sha": left["blob_sha"],
                            "reconstruction_blob_sha": right["blob_sha"],
                            "source_size": left["size"],
                            "reconstruction_size": right["size"],
                            "blob_sha_equal": equal,
                        }
                    )
                except (RuntimeError, TypeError, ValueError) as exc:
                    pair_errors.append(
                        {
                            "path": path,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

        compared_count = len(file_results)
        same_changed_file_set = bool(pair.get("same_changed_file_set", False))
        expected_shared = int(pair.get("shared_file_count", len(shared_files)))
        source_changed = int(pair.get("source_changed_file_count", 0))
        reconstruction_changed = int(pair.get("reconstruction_changed_file_count", 0))
        complete_observation = (
            not pair_errors
            and compared_count == expected_shared
            and compared_count == len(shared_files)
        )
        all_shared_blob_sha_equal = complete_observation and mismatch_count == 0
        full_changed_blob_equivalence = (
            all_shared_blob_sha_equal
            and same_changed_file_set
            and expected_shared == source_changed == reconstruction_changed
        )

        if pair_errors:
            outcome = "HOLD_INCOMPLETE"
        elif mismatch_count:
            outcome = "MISMATCH"
        elif full_changed_blob_equivalence:
            outcome = "MATCH_FULL_CHANGED_SET"
        elif all_shared_blob_sha_equal:
            outcome = "MATCH_SHARED_PATHS_ONLY"
        else:
            outcome = "HOLD_INCOMPLETE"

        measurement_seed = {
            "source_ref": source_ref,
            "source_head_sha": source_head,
            "reconstruction_ref": reconstruction_ref,
            "reconstruction_head_sha": reconstruction_head,
            "shared_files": list(shared_files),
            "source_filegraph_fingerprint": filegraph.get("fingerprint"),
        }
        measurements.append(
            {
                "measurement_id": f"measurement:{_stable_digest(measurement_seed)[:24]}",
                "measurement_kind": "reconstruction_blob_equivalence",
                "source_ref": source_ref,
                "source_head_sha": source_head,
                "reconstruction_ref": reconstruction_ref,
                "reconstruction_head_sha": reconstruction_head,
                "same_changed_file_set": same_changed_file_set,
                "expected_shared_file_count": expected_shared,
                "source_changed_file_count": source_changed,
                "reconstruction_changed_file_count": reconstruction_changed,
                "compared_file_count": compared_count,
                "blob_match_count": match_count,
                "blob_mismatch_count": mismatch_count,
                "error_count": len(pair_errors),
                "errors": pair_errors,
                "file_results": file_results,
                "all_shared_blob_sha_equal": all_shared_blob_sha_equal,
                "full_changed_blob_equivalence": full_changed_blob_equivalence,
                "outcome": outcome,
                "associated_request_ids": associated_request_ids,
                "request_satisfaction": "PARTIAL_STRUCTURAL_EVIDENCE",
                "request_fully_resolved": False,
                "remaining_required_evidence": [
                    "relevant exact-head tests",
                    "behavioral/semantic comparison where applicable",
                    "current-base freshness and governance review",
                ],
                "supersession_authority_granted": False,
                "boundary": (
                    "Git blob SHA equality proves byte identity for the measured file contents at the two exact heads. "
                    "It does not prove runtime behavior, test success, base freshness, merge readiness, or safe supersession."
                ),
            }
        )
        total_compared_files += compared_count
        total_blob_matches += match_count
        total_blob_mismatches += mismatch_count
        total_errors += len(pair_errors)

    measurements.sort(key=lambda row: (row["source_ref"], row["reconstruction_ref"]))
    outcome_counts: dict[str, int] = {}
    for row in measurements:
        outcome_counts[row["outcome"]] = outcome_counts.get(row["outcome"], 0) + 1

    payload: dict[str, Any] = {
        "schema": f"omega-pr-llmt-structural-measurements/v{STRUCTURAL_MEASUREMENT_SCHEMA_VERSION}",
        "source_filegraph_fingerprint": filegraph.get("fingerprint"),
        "source_requests_fingerprint": requests.get("fingerprint"),
        "measurement_kind": "reconstruction_blob_equivalence",
        "pair_count": len(measurements),
        "measurement_count": len(measurements),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "compared_file_count": total_compared_files,
        "blob_match_count": total_blob_matches,
        "blob_mismatch_count": total_blob_mismatches,
        "error_count": total_errors,
        "full_changed_blob_equivalence_count": sum(
            bool(row["full_changed_blob_equivalence"]) for row in measurements
        ),
        "associated_request_count": len(
            {
                request_id
                for row in measurements
                for request_id in row["associated_request_ids"]
            }
        ),
        "measurements": measurements,
        "authority": {
            "read": True,
            "write_authority_granted": False,
            "merge_authority_granted": False,
            "supersession_authority_granted": False,
        },
        "oak_boundaries": [
            "BLOB_SHA_EQUALITY == BYTE_IDENTITY_FOR_MEASURED_FILE_CONTENT",
            "BYTE_IDENTITY != BEHAVIORAL_EQUIVALENCE",
            "BYTE_IDENTITY != TEST_SUCCESS",
            "BYTE_IDENTITY != BASE_FRESHNESS",
            "BYTE_IDENTITY != MERGE_READINESS",
            "BYTE_IDENTITY != AUTOMATIC_SUPERSESSION",
            "PARTIAL_MEASUREMENT != FULL_REQUEST_RESOLUTION",
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
    parser = argparse.ArgumentParser(prog="omega-pr-llmt-measurements")
    parser.add_argument("filegraph")
    parser.add_argument("requests")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    filegraph = _load(args.filegraph)
    requests = _load(args.requests)
    source = GitHubPRSource(token=os.getenv(args.token_env) if args.token_env else None)
    payload = compile_reconstruction_blob_measurements(filegraph, requests, source)
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
