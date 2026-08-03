#!/usr/bin/env python3
"""OAKGate v1.0: deterministic ClaimGraph, evidence, freshness and policy gates."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator

ZERO_HASH = "0" * 64
SEVERITY = {"READY": 0, "WARNING": 1, "INCOMPLETE": 2, "FAILED": 3, "BLOCKED": 4, "CRITICAL": 5}
CLASS_ORDER = {"D": 0, "E": 1, "P": 2, "K": 3}
FRESHNESS_FIELDS = (
    "head_sha", "base_sha", "dependency_lock_hash",
    "test_definition_hash", "environment_hash",
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: str
    blocking: bool = False
    claim_id: str | None = None
    evidence_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    gate_id: str
    name: str
    status: str = "READY"
    severity: str = "READY"
    blocking: bool = False
    findings: list[Finding] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self, code: str, message: str, severity: str, *,
        blocking: bool = False, claim_id: str | None = None,
        evidence_id: str | None = None, action: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.findings.append(Finding(
            code, message, severity, blocking, claim_id, evidence_id, details or {}
        ))
        if action:
            self.actions.append(action)
        self.blocking = self.blocking or blocking
        if SEVERITY[severity] > SEVERITY[self.severity]:
            self.severity = severity
            self.status = code


def canonical_bytes(record: dict[str, Any]) -> bytes:
    payload = {
        key: value for key, value in record.items()
        if key != "record_sha256" and not key.startswith("_source_")
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def environment_hash() -> str:
    payload = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "runner_os": os.getenv("RUNNER_OS", ""),
        "runner_arch": os.getenv("RUNNER_ARCH", ""),
        "image_os": os.getenv("ImageOS", ""),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Object required in {path}")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Object required in {path}")
    return value


def load_jsonl(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"Ledger not found: {path}")
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{number}: {exc.msg}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{path}:{number}: object required")
                continue
            value["_source_path"] = str(path)
            value["_source_line"] = number
            records.append(value)
    return records, errors


def append_record(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    records, errors = load_jsonl([path]) if path.exists() else ([], [])
    if errors:
        raise ValueError("; ".join(errors))
    previous = records[-1]["record_sha256"] if records else ZERO_HASH
    record = dict(record)
    record["previous_record_sha256"] = previous
    record["record_sha256"] = record_hash(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def schema_gate(manifest: dict[str, Any], schemas: dict[str, dict[str, Any]]) -> GateResult:
    result = GateResult("G1", "Schema contracts")
    for error in sorted(
        Draft7Validator(schemas["manifest"]).iter_errors(manifest),
        key=lambda item: list(item.absolute_path),
    ):
        path = ".".join(map(str, error.absolute_path)) or "$"
        result.add("MANIFEST_SCHEMA_INVALID", f"{path}: {error.message}", "BLOCKED", blocking=True)
    validator = Draft7Validator(schemas["claim"])
    for index, claim in enumerate(manifest.get("claims", [])):
        for error in sorted(validator.iter_errors(claim), key=lambda item: list(item.absolute_path)):
            path = ".".join(map(str, error.absolute_path)) or "$"
            result.add(
                "CLAIM_SCHEMA_INVALID", f"claims[{index}].{path}: {error.message}",
                "BLOCKED", blocking=True, claim_id=str(claim.get("id", "")),
            )
    return result


def identity_gate(manifest: dict[str, Any], context: dict[str, Any], path: Path) -> GateResult:
    result = GateResult("G0", "Identity and runtime binding")
    expected = int(context["pr_id"])
    if manifest.get("pr_id") != expected:
        result.add("IDENTITY_PR_ID_MISMATCH", "Manifest PR number differs from context.", "BLOCKED", blocking=True)
    if manifest.get("title") != context["title"]:
        result.add("IDENTITY_TITLE_MISMATCH", "Manifest title differs from GitHub PR title.", "BLOCKED", blocking=True)
    expected_path = f".oak/active/pr_{expected}/manifest.json"
    if path.as_posix() != expected_path:
        result.add("IDENTITY_MANIFEST_PATH", f"Manifest must be {expected_path}.", "BLOCKED", blocking=True)
    if manifest.get("binding", {}).get("mode") != "runtime":
        result.add("IDENTITY_BINDING_MODE", "binding.mode must be runtime.", "BLOCKED", blocking=True)
    return result


def claim_gate(claims: list[dict[str, Any]]) -> GateResult:
    result = GateResult("G2", "ClaimGraph integrity")
    ids = [str(claim.get("id", "")) for claim in claims]
    for claim_id in sorted({item for item in ids if ids.count(item) > 1}):
        result.add("CLAIM_DUPLICATE_ID", f"Duplicate claim {claim_id}.", "BLOCKED", blocking=True, claim_id=claim_id)
    by_id = {str(claim["id"]): claim for claim in claims if claim.get("id")}
    graph = {claim_id: list(map(str, claim.get("depends_on", []))) for claim_id, claim in by_id.items()}
    for claim_id, dependencies in graph.items():
        if claim_id in dependencies:
            result.add("CLAIM_SELF_DEPENDENCY", f"{claim_id} depends on itself.", "BLOCKED", blocking=True, claim_id=claim_id)
        for dependency in dependencies:
            if dependency not in by_id:
                result.add("CLAIM_DEPENDENCY_MISSING", f"{claim_id} depends on unknown {dependency}.", "BLOCKED", blocking=True, claim_id=claim_id)
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for target in graph.get(node, []):
            if target not in graph:
                continue
            if state.get(target, 0) == 0:
                visit(target)
            elif state.get(target) == 1:
                cycle = stack[stack.index(target):] + [target]
                result.add(
                    "CLAIM_DEPENDENCY_CYCLE", " -> ".join(cycle), "BLOCKED",
                    blocking=True, action={"action": "break_claim_dependency_cycle", "claims": cycle[:-1]},
                )
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if state.get(node, 0) == 0:
            visit(node)
    return result


def ledger_gate(
    records: list[dict[str, Any]], schema: dict[str, Any], claim_ids: set[str],
) -> GateResult:
    result = GateResult("G3", "Evidence Ledger integrity")
    validator = Draft7Validator(schema)
    previous = ZERO_HASH
    if not records:
        result.add(
            "EVIDENCE_LEDGER_EMPTY", "No evidence record loaded.", "BLOCKED",
            blocking=True, action={"action": "generate_runtime_evidence", "automatic": True},
        )
        return result
    for record in records:
        clean = {key: value for key, value in record.items() if not key.startswith("_source_")}
        evidence_id = str(clean.get("evidence_id", ""))
        for error in sorted(validator.iter_errors(clean), key=lambda item: list(item.absolute_path)):
            path = ".".join(map(str, error.absolute_path)) or "$"
            result.add(
                "EVIDENCE_SCHEMA_INVALID", f"{evidence_id} {path}: {error.message}",
                "BLOCKED", blocking=True, evidence_id=evidence_id,
            )
        if clean.get("claim_id") not in claim_ids:
            result.add("EVIDENCE_ORPHAN", f"{evidence_id} references an unknown claim.", "BLOCKED", blocking=True, evidence_id=evidence_id)
        if clean.get("previous_record_sha256") != previous:
            result.add("EVIDENCE_CHAIN_BROKEN", f"{evidence_id} predecessor hash mismatch.", "BLOCKED", blocking=True, evidence_id=evidence_id)
        actual = record_hash(clean)
        if clean.get("record_sha256") != actual:
            result.add("EVIDENCE_HASH_MISMATCH", f"{evidence_id} record hash mismatch.", "BLOCKED", blocking=True, evidence_id=evidence_id)
        previous = str(clean.get("record_sha256", previous))
        if clean.get("status") == "pass" and clean.get("exit_code") not in (None, 0):
            result.add("EVIDENCE_CONTRADICTION", f"{evidence_id} is pass with non-zero exit.", "BLOCKED", blocking=True, evidence_id=evidence_id)
        if clean.get("status") == "fail" and clean.get("exit_code") == 0:
            result.add("EVIDENCE_CONTRADICTION", f"{evidence_id} is fail with zero exit.", "BLOCKED", blocking=True, evidence_id=evidence_id)
    return result


def freshness_gate(
    records: list[dict[str, Any]], claims: list[dict[str, Any]], context: dict[str, str],
) -> tuple[GateResult, dict[tuple[str, str], list[dict[str, Any]]]]:
    result = GateResult("G4", "Evidence freshness and coverage")
    fresh_passes: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for raw in records:
        record = {key: value for key, value in raw.items() if not key.startswith("_source_")}
        mismatches = [
            field for field in FRESHNESS_FIELDS
            if context.get(field) and record.get(field) != context[field]
        ]
        evidence_id = str(record.get("evidence_id", ""))
        claim_id = str(record.get("claim_id", ""))
        kind = str(record.get("kind", ""))
        if mismatches:
            result.add(
                "STALE_EVIDENCE", f"{evidence_id} stale on {', '.join(mismatches)}.",
                "WARNING", claim_id=claim_id, evidence_id=evidence_id,
            )
            continue
        if record.get("status") == "pass":
            fresh_passes.setdefault((claim_id, kind), []).append(record)
        elif record.get("status") == "fail":
            result.add("FRESH_EVIDENCE_FAILED", f"{evidence_id} failed.", "FAILED", blocking=True, claim_id=claim_id, evidence_id=evidence_id)
        else:
            result.add("FRESH_EVIDENCE_INCOMPLETE", f"{evidence_id} is {record.get('status')}.", "INCOMPLETE", claim_id=claim_id, evidence_id=evidence_id)
    for claim in claims:
        for kind in claim.get("evidence_required", []):
            if not fresh_passes.get((claim["id"], kind)):
                result.add(
                    "FRESH_EVIDENCE_MISSING", f"{claim['id']} lacks fresh {kind}.",
                    "BLOCKED", blocking=True, claim_id=claim["id"],
                    action={"action": "run_evidence_command", "claim_id": claim["id"], "kind": kind, "automatic": True},
                )
    return result, fresh_passes


def policy_gate(
    manifest: dict[str, Any], policy: dict[str, Any], changed_paths: list[str],
) -> GateResult:
    result = GateResult("G5", "Policy-as-code")
    pr_class = manifest["class"]
    class_policy = policy.get("classes", {}).get(pr_class)
    if not class_policy:
        result.add("POLICY_CLASS_UNKNOWN", f"No policy for class {pr_class}.", "BLOCKED", blocking=True)
        return result
    required = set(class_policy.get("requires", []))
    for claim in manifest.get("claims", []):
        missing = sorted(required - set(claim.get("evidence_required", [])))
        for kind in missing:
            result.add(
                "POLICY_EVIDENCE_NOT_DECLARED", f"{claim['id']} must declare {kind}.",
                "BLOCKED", blocking=True, claim_id=claim["id"],
            )
    for rule in policy.get("path_rules", []):
        matched = [path for path in changed_paths if fnmatch.fnmatch(path, rule["pattern"])]
        if not matched:
            continue
        minimum = rule.get("minimum_class", "D")
        if CLASS_ORDER[pr_class] < CLASS_ORDER[minimum]:
            result.add(
                "POLICY_PATH_CLASS_TOO_LOW", f"{rule['pattern']} requires {minimum}.",
                "BLOCKED", blocking=True, details={"paths": matched},
            )
        if rule.get("oak_self_review") and not manifest.get("self_review", {}).get("required"):
            result.add("OAK_SELF_REVIEW_MISSING", f"{rule['pattern']} requires self-review.", "BLOCKED", blocking=True)
    forbidden = set(policy.get("capabilities", {}).get("forbidden", []))
    for capability in sorted(forbidden & set(manifest.get("capabilities", {}).get("added", []))):
        result.add("POLICY_FORBIDDEN_CAPABILITY", f"Forbidden capability: {capability}.", "CRITICAL", blocking=True)
    if pr_class in {"K", "P"} and not manifest.get("rollback", {}).get("supported"):
        result.add("POLICY_ROLLBACK_REQUIRED", f"Class {pr_class} requires rollback.", "BLOCKED", blocking=True)
    return result


def evaluate(args: argparse.Namespace) -> int:
    manifest_path = args.manifest or Path(f".oak/active/pr_{args.pr_number}/manifest.json")
    manifest = load_json(manifest_path)
    schemas = {
        "manifest": load_json(args.schemas_dir / "pr_manifest.schema.json"),
        "claim": load_json(args.schemas_dir / "claim.schema.json"),
        "evidence": load_json(args.schemas_dir / "evidence_record.schema.json"),
    }
    policy = load_yaml(args.policy)
    context = {
        "pr_id": args.pr_number,
        "title": args.title,
        "head_sha": args.head_sha,
        "base_sha": args.base_sha,
        "dependency_lock_hash": sha256_file(args.requirements),
        "test_definition_hash": sha256_file(args.test_definition),
        "environment_hash": args.environment_hash,
    }
    ledgers = [Path(path) for path in manifest.get("evidence", {}).get("static_ledgers", [])] + args.runtime_ledger
    records, load_errors = load_jsonl(ledgers)
    gates = [
        identity_gate(manifest, context, manifest_path),
        schema_gate(manifest, schemas),
        claim_gate(manifest.get("claims", [])),
    ]
    g3 = ledger_gate(records, schemas["evidence"], {claim["id"] for claim in manifest.get("claims", [])})
    for error in load_errors:
        g3.add("EVIDENCE_LEDGER_LOAD_ERROR", error, "BLOCKED", blocking=True)
    gates.append(g3)
    g4, _ = freshness_gate(records, manifest.get("claims", []), context)
    gates.append(g4)
    gates.append(policy_gate(manifest, policy, read_lines(args.changed_paths_file)))

    maximum = max((SEVERITY[gate.severity] for gate in gates), default=0)
    blocking = any(gate.blocking for gate in gates)
    if blocking:
        verdict = next(gate.status for gate in gates if gate.blocking and SEVERITY[gate.severity] == maximum)
    elif maximum == 0:
        verdict = "READY_FOR_HUMAN_REVIEW"
    else:
        verdict = next(gate.status for gate in gates if SEVERITY[gate.severity] == maximum)

    penalties = {"WARNING": 4, "INCOMPLETE": 12, "FAILED": 25, "BLOCKED": 35, "CRITICAL": 50}
    score = max(0, 100 - sum(penalties.get(finding.severity, 0) for gate in gates for finding in gate.findings))
    actions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for gate in gates:
        for action in gate.actions:
            key = json.dumps(action, sort_keys=True)
            if key not in seen:
                seen.add(key)
                actions.append(action)
    payload = {
        "verdict": verdict,
        "severity": next(name for name, value in SEVERITY.items() if value == maximum),
        "blocking": blocking,
        "readiness_score": score,
        "gate_results": [asdict(gate) for gate in gates],
        "knowns": [
            f"{len(manifest.get('claims', []))} claims declared",
            f"{len(records)} evidence records inspected",
            f"{len(read_lines(args.changed_paths_file))} changed paths evaluated",
        ],
        "unknowns": ["runner_integrity_not_attested", "historical_calibration_not_available"],
        "next_actions": actions,
        "context": context,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "verdict.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# OAKGate v1.0 Verdict", "",
        f"- Verdict: **{verdict}**",
        f"- Severity: **{payload['severity']}**",
        f"- Blocking: **{str(blocking).lower()}**",
        f"- Readiness: **{score}/100**", "",
        "| Gate | Name | Status | Severity | Blocking | Findings |",
        "|---|---|---|---|---:|---:|",
    ]
    for gate in gates:
        lines.append(f"| {gate.gate_id} | {gate.name} | {gate.status} | {gate.severity} | {str(gate.blocking).lower()} | {len(gate.findings)} |")
    if actions:
        lines += ["", "## Next actions", ""] + [f"- `{item['action']}` — `{json.dumps(item, sort_keys=True)}`" for item in actions]
    (args.output_dir / "verdict.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (args.output_dir / "m_minus.jsonl").open("w", encoding="utf-8") as handle:
        for gate in gates:
            for finding in gate.findings:
                handle.write(json.dumps({
                    "gate": gate.gate_id, "code": finding.code, "severity": finding.severity,
                    "blocking": finding.blocking, "message": finding.message,
                    "claim_id": finding.claim_id, "evidence_id": finding.evidence_id,
                    "status": "observed",
                }, sort_keys=True) + "\n")
    print((args.output_dir / "verdict.md").read_text(encoding="utf-8"))
    return 1 if args.fail_on_blocked and blocking else 0


def read_lines(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    return sorted({line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()})


def record(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    env_hash = environment_hash()
    matching = [claim for claim in manifest["claims"] if args.kind in claim["evidence_required"]]
    if not matching:
        print(f"No claim requires {args.kind}.", file=sys.stderr)
        return 2
    for index, claim in enumerate(matching, 1):
        value = append_record(args.ledger, {
            "evidence_id": f"EVD-{manifest['pr_id']}-{args.kind.upper()}-{os.getenv('GITHUB_RUN_ID', 'LOCAL')}-{index:03d}",
            "claim_id": claim["id"], "kind": args.kind, "status": args.status,
            "producer": "github-actions" if os.getenv("GITHUB_ACTIONS") == "true" else "local",
            "head_sha": args.head_sha, "base_sha": args.base_sha,
            "dependency_lock_hash": sha256_file(args.requirements),
            "test_definition_hash": sha256_file(args.test_definition),
            "environment_hash": env_hash, "command": args.command,
            "exit_code": args.exit_code, "observed": args.observed,
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        print(json.dumps(value, sort_keys=True))
    if args.environment_file:
        args.environment_file.write_text(env_hash + "\n", encoding="utf-8")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="OAKGate v1.0")
    sub = root.add_subparsers(dest="command_name", required=True)

    rec = sub.add_parser("record")
    rec.add_argument("--manifest", type=Path, required=True)
    rec.add_argument("--ledger", type=Path, required=True)
    rec.add_argument("--kind", required=True)
    rec.add_argument("--status", choices=["pass", "fail", "inconclusive", "not_run"], required=True)
    rec.add_argument("--command", required=True)
    rec.add_argument("--observed", required=True)
    rec.add_argument("--exit-code", type=int, required=True)
    rec.add_argument("--head-sha", required=True)
    rec.add_argument("--base-sha", required=True)
    rec.add_argument("--requirements", type=Path, required=True)
    rec.add_argument("--test-definition", type=Path, required=True)
    rec.add_argument("--environment-file", type=Path)
    rec.set_defaults(func=record)

    ev = sub.add_parser("evaluate")
    ev.add_argument("--pr-number", type=int, required=True)
    ev.add_argument("--title", required=True)
    ev.add_argument("--head-sha", required=True)
    ev.add_argument("--base-sha", required=True)
    ev.add_argument("--manifest", type=Path)
    ev.add_argument("--runtime-ledger", type=Path, action="append", default=[])
    ev.add_argument("--changed-paths-file", type=Path)
    ev.add_argument("--policy", type=Path, default=Path(".oak/policy/policy.yaml"))
    ev.add_argument("--schemas-dir", type=Path, default=Path(".oak/schemas"))
    ev.add_argument("--requirements", type=Path, default=Path("00_oak_kernel/validation/requirements.txt"))
    ev.add_argument("--test-definition", type=Path, default=Path(".github/workflows/oak-pr-cartographer.yml"))
    ev.add_argument("--environment-hash", required=True)
    ev.add_argument("--output-dir", type=Path, default=Path("build/oakgate"))
    ev.add_argument("--fail-on-blocked", action="store_true")
    ev.set_defaults(func=evaluate)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"[OAKGATE-ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
