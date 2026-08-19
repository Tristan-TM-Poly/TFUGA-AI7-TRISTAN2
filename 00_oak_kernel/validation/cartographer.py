#!/usr/bin/env python3
"""OAK PR Cartographer: read-only PR manifest and evidence validator."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import requests
from jsonschema import Draft7Validator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ROOT = "https://api.github.com"
DEFAULT_API_VERSION = "2026-03-10"
BLOCKING = {"NEEDS_EVIDENCE", "CI_FAILED"}


class CartographerError(RuntimeError):
    pass


@dataclass(frozen=True)
class Finding:
    gate: str
    code: str
    severity: str
    message: str


@dataclass
class PRRecord:
    pr_id: int
    title: str
    html_url: str
    head_sha: str
    head_ref: str
    head_owner: str
    head_repo: str
    draft: bool
    manifest: Optional[dict[str, Any]] = None
    findings: list[Finding] = field(default_factory=list)
    check_summary: dict[str, int] = field(default_factory=dict)
    verdict: str = "UNASSESSED"
    action: str = "Inspecter"

    def add(self, gate: str, code: str, severity: str, message: str) -> None:
        self.findings.append(Finding(gate, code, severity, message))


class GitHubClient:
    def __init__(self, token: str, api_version: str, timeout: float = 30.0) -> None:
        if not token or token.lower() == "none":
            raise CartographerError("GITHUB_TOKEN absent.")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": api_version,
            "User-Agent": "AIT-PR-Cartographer/0.3",
        })
        retry = Retry(
            total=4,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get(self, url: str, *, params: Optional[Mapping[str, Any]] = None,
            allow_404: bool = False) -> Optional[requests.Response]:
        response = self.session.get(url, params=params, timeout=(5.0, self.timeout))
        if allow_404 and response.status_code == 404:
            return None
        if response.status_code in (403, 429):
            raise CartographerError(
                "Accès ou limite GitHub: "
                f"HTTP {response.status_code}; remaining="
                f"{response.headers.get('x-ratelimit-remaining', '?')}; "
                f"reset={response.headers.get('x-ratelimit-reset', '?')}."
            )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise CartographerError(
                f"GitHub API HTTP {response.status_code} pour {response.url}: "
                f"{response.text[:400].replace(chr(10), ' ')}"
            ) from exc
        return response

    def get_json(self, url: str, *, params: Optional[Mapping[str, Any]] = None,
                 allow_404: bool = False) -> Optional[dict[str, Any]]:
        response = self.get(url, params=params, allow_404=allow_404)
        if response is None:
            return None
        payload = response.json()
        if not isinstance(payload, dict):
            raise CartographerError(f"Objet JSON attendu pour {response.url}.")
        return payload

    def paginate(self, url: str, *, params: Optional[Mapping[str, Any]] = None,
                 wrapped_key: Optional[str] = None) -> Iterable[dict[str, Any]]:
        while url:
            response = self.get(url, params=params)
            assert response is not None
            payload = response.json()
            items = payload.get(wrapped_key) if wrapped_key and isinstance(payload, dict) else payload
            if not isinstance(items, list):
                raise CartographerError(f"Liste paginée attendue pour {response.url}.")
            yield from (item for item in items if isinstance(item, dict))
            url = response.links.get("next", {}).get("url", "")
            params = None

    def repo_file(self, owner: str, repo: str, path: str, ref: str) -> Optional[bytes]:
        payload = self.get_json(
            f"{API_ROOT}/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            allow_404=True,
        )
        if payload is None:
            return None
        if payload.get("type") != "file" or payload.get("encoding") != "base64":
            raise CartographerError(f"Fichier GitHub inattendu: {path}@{ref}.")
        try:
            return base64.b64decode(str(payload["content"]))
        except Exception as exc:
            raise CartographerError(f"Base64 invalide: {path}@{ref}.") from exc


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CartographerError(f"Schéma illisible {path}: {exc}") from exc
    Draft7Validator.check_schema(schema)
    return schema


def error_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return f"{path}: {error.message}"


def schema_errors(value: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = Draft7Validator(schema).iter_errors(value)
    return [error_path(e) for e in sorted(errors, key=lambda e: list(e.absolute_path))]


def parse_ledger(raw: bytes, evidence_schema: Optional[dict[str, Any]] = None
                 ) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return [], [f"UTF-8 invalide: {exc}"]
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    validator = Draft7Validator(evidence_schema) if evidence_schema else None
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"ligne {number}: JSON invalide: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"ligne {number}: objet JSON attendu")
            continue
        missing = {"claim_id", "kind", "status"} - set(record)
        if missing:
            errors.append(f"ligne {number}: champs manquants {sorted(missing)}")
            continue
        if record["status"] not in {"pass", "fail", "inconclusive", "not_run"}:
            errors.append(f"ligne {number}: status invalide {record['status']!r}")
            continue
        item_errors = sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)) if validator else []
        if item_errors:
            errors.extend(f"ligne {number}: {error_path(e)}" for e in item_errors)
            continue
        records.append(record)
    if not records and not errors:
        errors.append("ledger vide")
    return records, errors


def collect_cycles(graph: Mapping[int, list[int]]) -> list[list[int]]:
    cycles: list[list[int]] = []
    state: dict[int, int] = {}
    stack: list[int] = []

    def visit(node: int) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in graph:
                continue
            if state.get(nxt, 0) == 0:
                visit(nxt)
            elif state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):] + [nxt]
                core = cycle[:-1]
                pivot = min(range(len(core)), key=core.__getitem__)
                canonical = core[pivot:] + core[:pivot] + [core[pivot]]
                if canonical not in cycles:
                    cycles.append(canonical)
        stack.pop()
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node)
    return cycles


def summarize_checks(runs: list[dict[str, Any]]) -> dict[str, int]:
    out = {key: 0 for key in ("total", "queued", "in_progress", "success", "failure", "neutral", "other")}
    failures = {"failure", "cancelled", "timed_out", "action_required", "startup_failure", "stale"}
    for run in runs:
        out["total"] += 1
        status, conclusion = run.get("status"), run.get("conclusion")
        if status in {"queued", "in_progress"}:
            out[str(status)] += 1
        elif conclusion == "success":
            out["success"] += 1
        elif conclusion in failures:
            out["failure"] += 1
        elif conclusion in {"neutral", "skipped"}:
            out["neutral"] += 1
        else:
            out["other"] += 1
    return out


def set_verdict(record: PRRecord) -> None:
    codes = {f.code for f in record.findings}
    rules = [
        ("MANIFEST_MISSING", "BLOCKED_MANIFEST_MISSING", "Ajouter le manifeste"),
        ("SCHEMA_INVALID", "BLOCKED_SCHEMA", "Corriger le manifeste"),
        ("IDENTITY_", "BLOCKED_IDENTITY", "Réaligner PR et manifeste"),
        ("DEPENDENCY_", "BLOCKED_DEPENDENCY", "Corriger les dépendances"),
        ("EVIDENCE_", "NEEDS_EVIDENCE", "Réparer les preuves"),
        ("CHECKS_FAILED", "CI_FAILED", "Corriger les checks"),
    ]
    for marker, verdict, action in rules:
        if any(code == marker or code.startswith(marker) for code in codes):
            record.verdict, record.action = verdict, action
            return
    if record.draft:
        record.verdict, record.action = "DRAFT", "Finaliser la PR"
    elif {"CHECKS_PENDING", "CHECKS_ABSENT"} & codes:
        record.verdict, record.action = "PENDING_CI", "Attendre OAKGate"
    else:
        record.verdict, record.action = "READY_FOR_HUMAN_REVIEW", "Revue humaine"


def evaluate(client: GitHubClient, owner: str, repo: str, manifest_schema: dict[str, Any],
             evidence_schema: dict[str, Any], manifest_path: str = "pr_manifest.json",
             pr_number: Optional[int] = None) -> list[PRRecord]:
    pulls_url = f"{API_ROOT}/repos/{owner}/{repo}/pulls"
    if pr_number is None:
        pulls = list(client.paginate(pulls_url, params={"state": "open", "per_page": 100}))
    else:
        pull = client.get_json(f"{pulls_url}/{pr_number}", allow_404=True)
        if pull is None:
            raise CartographerError(f"Pull Request #{pr_number} introuvable.")
        pulls = [pull]

    records: list[PRRecord] = []
    by_id: dict[int, PRRecord] = {}
    for pull in pulls:
        head = pull["head"]
        head_repo = str((head.get("repo") or {}).get("full_name") or f"{owner}/{repo}")
        head_owner, head_name = head_repo.split("/", 1)
        record = PRRecord(
            int(pull["number"]), str(pull.get("title", "")), str(pull.get("html_url", "")),
            str(head["sha"]), str(head["ref"]), head_owner, head_name, bool(pull.get("draft")),
        )
        records.append(record)
        by_id[record.pr_id] = record

        raw = client.repo_file(head_owner, head_name, manifest_path, record.head_sha)
        if raw is None:
            record.add("G1", "MANIFEST_MISSING", "error", f"{manifest_path} absent au SHA de tête.")
            continue
        try:
            manifest = json.loads(raw.decode("utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("objet JSON attendu")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            record.add("G1", "SCHEMA_INVALID", "error", str(exc))
            continue
        record.manifest = manifest
        errors = schema_errors(manifest, manifest_schema)
        for message in errors:
            record.add("G1", "SCHEMA_INVALID", "error", message)
        if errors:
            continue

        if manifest["pr_id"] != record.pr_id:
            record.add("G2", "IDENTITY_PR_ID_MISMATCH", "error", "pr_id différent du numéro GitHub.")
        if manifest["title"] != record.title:
            record.add("G2", "IDENTITY_TITLE_MISMATCH", "error", "Titre différent du titre GitHub.")
        expected_path = f"evidence/pr_{record.pr_id}.jsonl"
        ledger_path = manifest["evidence"]["ledger_path"]
        if ledger_path != expected_path:
            record.add("G2", "IDENTITY_LEDGER_PATH_MISMATCH", "error", f"Chemin attendu: {expected_path}.")

        required = manifest["dependencies"]["required_prs"]
        supersedes = manifest["dependencies"]["supersedes"]
        if record.pr_id in required or record.pr_id in supersedes:
            record.add("G3", "DEPENDENCY_SELF_REFERENCE", "error", "Auto-dépendance interdite.")
        if set(required) & set(supersedes):
            record.add("G3", "DEPENDENCY_ROLE_CONFLICT", "error", "Dépendance aussi déclarée comme remplacée.")

        ledger_raw = client.repo_file(head_owner, head_name, ledger_path, record.head_sha)
        if ledger_raw is None:
            record.add("G4", "EVIDENCE_LEDGER_MISSING", "error", f"{ledger_path} absent.")
        else:
            actual = hashlib.sha256(ledger_raw).hexdigest()
            if actual != manifest["evidence"]["ledger_sha256"]:
                record.add("G4", "EVIDENCE_HASH_MISMATCH", "error", f"SHA-256 obtenu: {actual}.")
            ledger, ledger_errors = parse_ledger(ledger_raw, evidence_schema)
            for message in ledger_errors:
                record.add("G4", "EVIDENCE_LEDGER_INVALID", "error", message)
            claim_id = manifest["claim"]["id"]
            claim_records = [item for item in ledger if item.get("claim_id") == claim_id]
            kinds = {str(item.get("kind")) for item in claim_records}
            missing = sorted(set(manifest["evidence"]["required_kinds"]) - kinds)
            if missing:
                record.add("G4", "EVIDENCE_KIND_MISSING", "error", f"Types absents: {missing}.")
            if any(item.get("status") == "fail" for item in claim_records):
                record.add("G4", "EVIDENCE_CONTRADICTS_CLAIM", "error", "Une preuve contredit le claim.")
            if any(item.get("status") in {"inconclusive", "not_run"} for item in claim_records):
                record.add("G4", "EVIDENCE_INCONCLUSIVE", "warning", "Preuve non concluante présente.")

        runs = list(client.paginate(
            f"{API_ROOT}/repos/{owner}/{repo}/commits/{record.head_sha}/check-runs",
            params={"per_page": 100}, wrapped_key="check_runs",
        ))
        record.check_summary = summarize_checks(runs)
        if not runs:
            record.add("G5", "CHECKS_ABSENT", "warning", "Aucun Check Run.")
        elif record.check_summary["failure"]:
            record.add("G5", "CHECKS_FAILED", "error", "Au moins un check est en échec.")
        elif record.check_summary["queued"] + record.check_summary["in_progress"] + record.check_summary["other"]:
            record.add("G5", "CHECKS_PENDING", "warning", "Checks incomplets.")

    graph = {
        r.pr_id: list(r.manifest["dependencies"]["required_prs"])
        for r in records if r.manifest and not any(f.code == "SCHEMA_INVALID" for f in r.findings)
    }
    dependency_cache: dict[int, Optional[dict[str, Any]]] = {}
    for record in records:
        for dep in graph.get(record.pr_id, []):
            if dep not in dependency_cache:
                dependency_cache[dep] = client.get_json(f"{pulls_url}/{dep}", allow_404=True)
            payload = dependency_cache[dep]
            if payload is None:
                record.add("G3", "DEPENDENCY_NOT_FOUND", "error", f"PR #{dep} introuvable.")
            elif payload.get("merged_at"):
                pass
            elif payload.get("state") == "open":
                record.add("G3", "DEPENDENCY_NOT_MERGED", "warning", f"PR #{dep} encore ouverte.")
            else:
                record.add("G3", "DEPENDENCY_CLOSED_UNMERGED", "error", f"PR #{dep} fermée sans fusion.")
    for cycle in collect_cycles(graph):
        for node in set(cycle[:-1]):
            if node in by_id:
                by_id[node].add("G3", "DEPENDENCY_CYCLE", "error", " → ".join(map(str, cycle)))
    for record in records:
        set_verdict(record)
    return sorted(records, key=lambda r: r.pr_id)


def write_outputs(records: list[PRRecord], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pr_registry.json").write_text(
        json.dumps([asdict(r) for r in records], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "| PR | Titre | Classe | Produit | Checks | Verdict OAK | Action |",
        "|---:|---|:---:|---|---|---|---|",
    ]
    for r in records:
        manifest = r.manifest or {}
        checks = r.check_summary
        check_text = f"{checks.get('success', 0)}✓/{checks.get('failure', 0)}✗/{checks.get('queued', 0) + checks.get('in_progress', 0)}…"
        title = r.title.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| [#{r.pr_id}]({r.html_url}) | {title} | {manifest.get('class', '?')} | "
            f"{manifest.get('product', '?')} | {check_text} | **{r.verdict}** | {r.action} |"
        )
    (output_dir / "pr_registry.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (output_dir / "m_minus.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            for finding in record.findings:
                if finding.severity in {"warning", "error"}:
                    handle.write(json.dumps({
                        "pr_id": record.pr_id,
                        "head_sha": record.head_sha,
                        **asdict(finding),
                    }, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cartographie OAK des Pull Requests.")
    parser.add_argument("--owner", default=os.getenv("GITHUB_REPOSITORY_OWNER", "Tristan-TM-Poly"))
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2").split("/")[-1])
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--api-version", default=os.getenv("GITHUB_API_VERSION", DEFAULT_API_VERSION))
    parser.add_argument("--schema", type=Path, default=Path(__file__).with_name("pr_manifest.schema.json"))
    parser.add_argument("--evidence-schema", type=Path, default=Path(__file__).with_name("evidence_record.schema.json"))
    parser.add_argument("--manifest-path", default="pr_manifest.json")
    parser.add_argument("--output-dir", type=Path, default=Path("build/oak_cartography"))
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        records = evaluate(
            GitHubClient(args.token, args.api_version), args.owner, args.repo,
            load_schema(args.schema), load_schema(args.evidence_schema),
            args.manifest_path, args.pr_number,
        )
        write_outputs(records, args.output_dir)
    except (CartographerError, requests.RequestException) as exc:
        print(f"[OAK-CARTOGRAPHER-ERROR] {exc}", file=sys.stderr)
        return 2
    blocked = [r for r in records if r.verdict.startswith("BLOCKED") or r.verdict in BLOCKING]
    print((args.output_dir / "pr_registry.md").read_text(encoding="utf-8"))
    print(f"PR analysées: {len(records)}; bloquées: {len(blocked)}")
    return 1 if args.fail_on_blocked and blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
