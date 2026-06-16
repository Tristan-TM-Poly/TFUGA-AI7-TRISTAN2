#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: AT-1 External Orchestrator

Guarded multi-connector orchestration for ChatGPT/Gemini + Google Drive,
Dropbox, GitHub, Vercel, and Render.

Design locks
------------
- No secrets in code. All tokens are read from environment variables.
- Dry-run by default. Write/deploy actions require --execute.
- OAK gate first: external actions are blocked unless local OAK reports are CANON,
  except for read-only observation and issue/report creation.
- LLMs return JSON decisions only; the orchestrator sanitizes allowed actions.
- Destructive actions are not implemented.

This file intentionally uses Python stdlib only. Optional provider SDKs can be
added later behind the same adapter interface.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "external_orchestration"
REPORT_PATH = REPORT_DIR / "at1_external_orchestrator_report.json"
OAK_REPORT = ROOT / "omega_max_oak_report.json"
AUTO_GENESIS_REPORT = ROOT / "reports" / "auto_genesis" / "auto_genesis_report.json"
SAGE_REPORT = ROOT / "reports" / "sage" / "sage_orchestrator_report.json"

ALLOWED_ACTIONS = {
    "none",
    "create_github_issue",
    "upload_report_to_drive",
    "upload_report_to_dropbox",
    "list_github_repo",
    "list_drive_files",
    "list_dropbox_folder",
    "list_vercel_projects",
    "list_render_services",
    "trigger_vercel_deploy_hook",
    "trigger_render_deploy",
}

WRITE_ACTIONS = {
    "create_github_issue",
    "upload_report_to_drive",
    "upload_report_to_dropbox",
    "trigger_vercel_deploy_hook",
    "trigger_render_deploy",
}

DEPLOY_ACTIONS = {"trigger_vercel_deploy_hook", "trigger_render_deploy"}


@dataclass
class OrchestrationEvent:
    action: str
    provider: str
    status: str
    dry_run: bool
    detail: Dict[str, Any]


def now() -> float:
    return time.time()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def request_json(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any] | bytes] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    data: Optional[bytes]
    final_headers = dict(headers or {})
    if isinstance(payload, bytes):
        data = payload
    elif payload is None:
        data = None
    else:
        data = json.dumps(payload).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=final_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return {"status": response.status}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"status": response.status, "text": raw[:4000]}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")[:4000]
        return {"_error": f"HTTP {exc.code}", "body": text, "url": url}
    except urllib.error.URLError as exc:
        return {"_error": str(exc), "url": url}


def oak_is_canon() -> bool:
    report = read_json(OAK_REPORT)
    if not report or "results" not in report:
        return False
    results = report.get("results", [])
    return bool(results) and all(item.get("verdict") == "CANON" and float(item.get("oak_score", 0.0)) >= 80.0 for item in results)


def collect_context() -> Dict[str, Any]:
    return {
        "repo_root": str(ROOT),
        "oak_is_canon": oak_is_canon(),
        "oak_report": read_json(OAK_REPORT),
        "auto_genesis_report": read_json(AUTO_GENESIS_REPORT),
        "sage_report": read_json(SAGE_REPORT),
        "available_reports": [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reports").glob("**/*.json"))] if (ROOT / "reports").exists() else [],
    }


def sanitize_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    action = decision.get("action", "none")
    if action not in ALLOWED_ACTIONS:
        action = "none"
    clean = {
        "action": action,
        "provider": str(decision.get("provider", "local")),
        "title": str(decision.get("title", "AT-1 External Orchestration"))[:200],
        "body": str(decision.get("body", ""))[:60000],
        "target": str(decision.get("target", ""))[:1000],
        "metadata": decision.get("metadata", {}) if isinstance(decision.get("metadata", {}), dict) else {},
    }
    return clean


def deterministic_decision(context: Dict[str, Any]) -> Dict[str, Any]:
    if not context.get("oak_is_canon"):
        return {
            "action": "create_github_issue",
            "provider": "github",
            "title": "[OAK/SAGE] External orchestration blocked: local CANON gate is not satisfied",
            "body": "The AT-1 external orchestrator detected that the local OAK report is missing or not fully CANON. External write/deploy actions are blocked until omega_max_oak_report.json reports CANON with OAK >= 80 for all benchmark results.",
            "target": "repo:issues",
            "metadata": {"oak_is_canon": False},
        }
    return {
        "action": "none",
        "provider": "local",
        "title": "AT-1 external orchestration observation complete",
        "body": "OAK is CANON. No external action was required by deterministic fallback.",
        "target": "reports/external_orchestration",
        "metadata": {"oak_is_canon": True},
    }


def call_gemini_decision(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    if not api_key:
        return None
    prompt = (
        "You are AT-1 SAGE. Return strict JSON only with keys: "
        "action, provider, title, body, target, metadata. Allowed actions: "
        + ", ".join(sorted(ALLOWED_ACTIONS))
        + ". Do not request destructive actions. Context: "
        + json.dumps(context, ensure_ascii=False, sort_keys=True)[:28000]
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = request_json("POST", url, {"x-goog-api-key": api_key, "Content-Type": "application/json"}, payload)
    try:
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
    except Exception:
        return {"action": "none", "provider": "gemini", "title": "Gemini decision parse failed", "body": json.dumps(response)[:4000], "target": "local", "metadata": {"parse_failed": True}}


def create_github_issue(title: str, body: str, dry_run: bool) -> OrchestrationEvent:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if dry_run:
        return OrchestrationEvent("create_github_issue", "github", "dry_run", True, {"repo": repo, "title": title})
    if not repo or not token:
        return OrchestrationEvent("create_github_issue", "github", "blocked", False, {"reason": "missing GITHUB_REPOSITORY or GITHUB_TOKEN"})
    result = request_json(
        "POST",
        f"https://api.github.com/repos/{repo}/issues",
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        {"title": title, "body": body, "labels": ["AT-1", "SAGE", "orchestration"]},
    )
    status = "error" if "_error" in result else "ok"
    return OrchestrationEvent("create_github_issue", "github", status, False, result)


def list_github_repo(dry_run: bool) -> OrchestrationEvent:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GITHUB_TOKEN")
    if dry_run:
        return OrchestrationEvent("list_github_repo", "github", "dry_run", True, {"repo": repo})
    if not repo or not token:
        return OrchestrationEvent("list_github_repo", "github", "blocked", False, {"reason": "missing GITHUB_REPOSITORY or GITHUB_TOKEN"})
    result = request_json("GET", f"https://api.github.com/repos/{repo}", {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    return OrchestrationEvent("list_github_repo", "github", "error" if "_error" in result else "ok", False, result)


def upload_to_drive(local_path: Path, dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
    if dry_run:
        return OrchestrationEvent("upload_report_to_drive", "google_drive", "dry_run", True, {"path": str(local_path)})
    if not token:
        return OrchestrationEvent("upload_report_to_drive", "google_drive", "blocked", False, {"reason": "missing GOOGLE_DRIVE_ACCESS_TOKEN"})
    if not local_path.exists():
        return OrchestrationEvent("upload_report_to_drive", "google_drive", "blocked", False, {"reason": "missing local file", "path": str(local_path)})
    mime = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=media"
    result = request_json("POST", url, {"Authorization": f"Bearer {token}", "Content-Type": mime}, local_path.read_bytes())
    return OrchestrationEvent("upload_report_to_drive", "google_drive", "error" if "_error" in result else "ok", False, result)


def upload_to_dropbox(local_path: Path, dropbox_path: str, dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    if dry_run:
        return OrchestrationEvent("upload_report_to_dropbox", "dropbox", "dry_run", True, {"path": str(local_path), "dropbox_path": dropbox_path})
    if not token:
        return OrchestrationEvent("upload_report_to_dropbox", "dropbox", "blocked", False, {"reason": "missing DROPBOX_ACCESS_TOKEN"})
    if not local_path.exists():
        return OrchestrationEvent("upload_report_to_dropbox", "dropbox", "blocked", False, {"reason": "missing local file", "path": str(local_path)})
    args = {"path": dropbox_path, "mode": "overwrite", "autorename": False, "mute": False}
    result = request_json(
        "POST",
        "https://content.dropboxapi.com/2/files/upload",
        {"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps(args), "Content-Type": "application/octet-stream"},
        local_path.read_bytes(),
    )
    return OrchestrationEvent("upload_report_to_dropbox", "dropbox", "error" if "_error" in result else "ok", False, result)


def list_drive_files(dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
    if dry_run:
        return OrchestrationEvent("list_drive_files", "google_drive", "dry_run", True, {})
    if not token:
        return OrchestrationEvent("list_drive_files", "google_drive", "blocked", False, {"reason": "missing GOOGLE_DRIVE_ACCESS_TOKEN"})
    url = "https://www.googleapis.com/drive/v3/files?pageSize=10&fields=files(id,name,mimeType,modifiedTime)"
    result = request_json("GET", url, {"Authorization": f"Bearer {token}"})
    return OrchestrationEvent("list_drive_files", "google_drive", "error" if "_error" in result else "ok", False, result)


def list_dropbox_folder(dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    path = os.environ.get("DROPBOX_ORCH_PATH", "")
    if dry_run:
        return OrchestrationEvent("list_dropbox_folder", "dropbox", "dry_run", True, {"path": path})
    if not token:
        return OrchestrationEvent("list_dropbox_folder", "dropbox", "blocked", False, {"reason": "missing DROPBOX_ACCESS_TOKEN"})
    result = request_json("POST", "https://api.dropboxapi.com/2/files/list_folder", {"Authorization": f"Bearer {token}"}, {"path": path, "limit": 10})
    return OrchestrationEvent("list_dropbox_folder", "dropbox", "error" if "_error" in result else "ok", False, result)


def list_vercel_projects(dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("VERCEL_TOKEN")
    team_id = os.environ.get("VERCEL_TEAM_ID")
    query = f"?teamId={urllib.parse.quote(team_id)}" if team_id else ""
    if dry_run:
        return OrchestrationEvent("list_vercel_projects", "vercel", "dry_run", True, {"team_id": bool(team_id)})
    if not token:
        return OrchestrationEvent("list_vercel_projects", "vercel", "blocked", False, {"reason": "missing VERCEL_TOKEN"})
    result = request_json("GET", f"https://api.vercel.com/v9/projects{query}", {"Authorization": f"Bearer {token}"})
    return OrchestrationEvent("list_vercel_projects", "vercel", "error" if "_error" in result else "ok", False, result)


def trigger_vercel_deploy_hook(dry_run: bool) -> OrchestrationEvent:
    hook_url = os.environ.get("VERCEL_DEPLOY_HOOK_URL")
    if dry_run:
        return OrchestrationEvent("trigger_vercel_deploy_hook", "vercel", "dry_run", True, {"has_hook": bool(hook_url)})
    if not hook_url:
        return OrchestrationEvent("trigger_vercel_deploy_hook", "vercel", "blocked", False, {"reason": "missing VERCEL_DEPLOY_HOOK_URL"})
    result = request_json("POST", hook_url, {}, None)
    return OrchestrationEvent("trigger_vercel_deploy_hook", "vercel", "error" if "_error" in result else "ok", False, result)


def list_render_services(dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("RENDER_API_KEY")
    if dry_run:
        return OrchestrationEvent("list_render_services", "render", "dry_run", True, {})
    if not token:
        return OrchestrationEvent("list_render_services", "render", "blocked", False, {"reason": "missing RENDER_API_KEY"})
    result = request_json("GET", "https://api.render.com/v1/services?limit=10", {"Authorization": f"Bearer {token}", "Accept": "application/json"})
    return OrchestrationEvent("list_render_services", "render", "error" if "_error" in result else "ok", False, result)


def trigger_render_deploy(dry_run: bool) -> OrchestrationEvent:
    token = os.environ.get("RENDER_API_KEY")
    service_id = os.environ.get("RENDER_SERVICE_ID")
    if dry_run:
        return OrchestrationEvent("trigger_render_deploy", "render", "dry_run", True, {"has_service_id": bool(service_id)})
    if not token or not service_id:
        return OrchestrationEvent("trigger_render_deploy", "render", "blocked", False, {"reason": "missing RENDER_API_KEY or RENDER_SERVICE_ID"})
    result = request_json("POST", f"https://api.render.com/v1/services/{urllib.parse.quote(service_id)}/deploys", {"Authorization": f"Bearer {token}", "Accept": "application/json"}, {})
    return OrchestrationEvent("trigger_render_deploy", "render", "error" if "_error" in result else "ok", False, result)


def execute_decision(decision: Dict[str, Any], dry_run: bool, force: bool) -> OrchestrationEvent:
    action = decision["action"]
    if action in WRITE_ACTIONS and not dry_run and not force:
        return OrchestrationEvent(action, decision.get("provider", "unknown"), "blocked", False, {"reason": "write action requires --force-write"})
    if action in DEPLOY_ACTIONS and not dry_run and os.environ.get("AT1_ALLOW_DEPLOY") != "1":
        return OrchestrationEvent(action, decision.get("provider", "unknown"), "blocked", False, {"reason": "deploy action requires AT1_ALLOW_DEPLOY=1"})
    if action in WRITE_ACTIONS and not oak_is_canon() and action != "create_github_issue":
        return OrchestrationEvent(action, decision.get("provider", "unknown"), "blocked", dry_run, {"reason": "OAK gate not CANON"})

    if action == "none":
        return OrchestrationEvent("none", "local", "ok", dry_run, {"message": "no external action selected"})
    if action == "create_github_issue":
        return create_github_issue(decision.get("title", "AT-1 Issue"), decision.get("body", ""), dry_run)
    if action == "list_github_repo":
        return list_github_repo(dry_run)
    if action == "upload_report_to_drive":
        return upload_to_drive(REPORT_PATH, dry_run)
    if action == "upload_report_to_dropbox":
        return upload_to_dropbox(REPORT_PATH, os.environ.get("DROPBOX_REPORT_PATH", "/at1_external_orchestrator_report.json"), dry_run)
    if action == "list_drive_files":
        return list_drive_files(dry_run)
    if action == "list_dropbox_folder":
        return list_dropbox_folder(dry_run)
    if action == "list_vercel_projects":
        return list_vercel_projects(dry_run)
    if action == "trigger_vercel_deploy_hook":
        return trigger_vercel_deploy_hook(dry_run)
    if action == "list_render_services":
        return list_render_services(dry_run)
    if action == "trigger_render_deploy":
        return trigger_render_deploy(dry_run)
    return OrchestrationEvent(action, decision.get("provider", "unknown"), "blocked", dry_run, {"reason": "unhandled action"})


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AT-1 guarded multi-connector orchestrator")
    parser.add_argument("--execute", action="store_true", help="execute selected action; default is dry-run")
    parser.add_argument("--force-write", action="store_true", help="allow non-deploy write actions when --execute is set")
    parser.add_argument("--action", choices=sorted(ALLOWED_ACTIONS), default=None, help="override LLM/deterministic action")
    parser.add_argument("--provider", default=None, help="provider override for manual action")
    parser.add_argument("--title", default=None, help="manual issue/action title")
    parser.add_argument("--body", default=None, help="manual issue/action body")
    parser.add_argument("--use-gemini", action="store_true", help="ask Gemini for strict JSON decision when GEMINI_API_KEY is present")
    args = parser.parse_args(argv)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    dry_run = not args.execute
    context = collect_context()

    if args.action:
        decision = sanitize_decision({
            "action": args.action,
            "provider": args.provider or "manual",
            "title": args.title or f"AT-1 {args.action}",
            "body": args.body or "Manual AT-1 orchestrator action.",
            "target": "manual",
            "metadata": {"manual": True},
        })
    elif args.use_gemini:
        decision = sanitize_decision(call_gemini_decision(context) or deterministic_decision(context))
    else:
        decision = sanitize_decision(deterministic_decision(context))

    event = execute_decision(decision, dry_run=dry_run, force=args.force_write)
    report = {
        "system": "AT-1 External Orchestrator",
        "created_at_unix": now(),
        "dry_run": dry_run,
        "oak_is_canon": context.get("oak_is_canon"),
        "decision": decision,
        "event": asdict(event),
        "enabled_env": {
            "github": bool(os.environ.get("GITHUB_TOKEN")),
            "google_drive": bool(os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")),
            "dropbox": bool(os.environ.get("DROPBOX_ACCESS_TOKEN")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
            "vercel": bool(os.environ.get("VERCEL_TOKEN") or os.environ.get("VERCEL_DEPLOY_HOOK_URL")),
            "render": bool(os.environ.get("RENDER_API_KEY")),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if event.status in {"ok", "dry_run", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
