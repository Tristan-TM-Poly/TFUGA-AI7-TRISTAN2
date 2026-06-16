#!/usr/bin/env python3
"""
TTM-TFUGA-AI7-TRISTAN2 :: SAGE Orchestrator

Guarded orchestration layer for OAK regressions.

SAGE reads local reports, detects regressions, optionally calls an external LLM
endpoint for structured diagnosis, and can create GitHub Issues. It does not edit
code, does not open PRs, and defaults to dry-run.

Environment variables
---------------------
GITHUB_REPOSITORY      owner/repo, usually provided by GitHub Actions
GITHUB_TOKEN           token with Issues write permission, only needed with --create-issue
SAGE_LLM_ENDPOINT      optional HTTP endpoint for LLM diagnosis
SAGE_LLM_API_KEY       optional API key for the LLM endpoint
SAGE_LLM_MODEL         optional model name passed to the endpoint

Usage
-----
python core/sage_orchestrator.py --dry-run
python core/sage_orchestrator.py --create-issue
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OAK_REPORT = ROOT / "omega_max_oak_report.json"
AUTO_GENESIS_REPORT = ROOT / "reports" / "auto_genesis" / "auto_genesis_report.json"
BASELINE_REPORT = ROOT / "reports" / "baselines" / "baseline_comparison.json"
M_MINUS_REGISTRY = ROOT / "reports" / "auto_genesis" / "m_minus_registry.json"
SAGE_REPORT_DIR = ROOT / "reports" / "sage"
SAGE_REPORT = SAGE_REPORT_DIR / "sage_orchestrator_report.json"


@dataclass
class RegressionFinding:
    source: str
    severity: str
    title: str
    evidence: Dict[str, Any]
    suggested_action: str


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def detect_oak_regressions(report: Optional[Dict[str, Any]]) -> List[RegressionFinding]:
    findings: List[RegressionFinding] = []
    if not report:
        findings.append(RegressionFinding(
            source="omega_max_oak_report.json",
            severity="high",
            title="[SAGE] Missing OAK benchmark report",
            evidence={"path": str(OAK_REPORT.relative_to(ROOT))},
            suggested_action="Run prototypes/omega_max_benchmark.py before SAGE orchestration.",
        ))
        return findings

    for item in report.get("results", []):
        benchmark = item.get("benchmark", "unknown")
        verdict = item.get("verdict", "unknown")
        score = float(item.get("oak_score", 0.0))
        if verdict != "CANON" or score < 80.0:
            findings.append(RegressionFinding(
                source="omega_max_oak_report.json",
                severity="critical" if verdict == "M_MINUS" else "medium",
                title=f"[OAK Regression] {benchmark} downgraded to {verdict} ({score:.2f})",
                evidence={
                    "benchmark": benchmark,
                    "relation_type": item.get("relation_type"),
                    "verdict": verdict,
                    "oak_score": score,
                    "errors": item.get("errors", {}),
                    "extracted": item.get("extracted", {}),
                    "ground_truth": item.get("ground_truth", {}),
                },
                suggested_action="Inspect estimator drift, recent code changes, and M_MINUS failure signature.",
            ))
    return findings


def detect_baseline_regressions(report: Optional[Dict[str, Any]]) -> List[RegressionFinding]:
    findings: List[RegressionFinding] = []
    if not report:
        return findings

    # Supports both the compact dict style and the larger results/list style.
    if "results" in report and isinstance(report["results"], list):
        for suite in report["results"]:
            name = suite.get("benchmark", "unknown")
            for row in suite.get("rows", []):
                verdict = row.get("verdict")
                drift = float(row.get("mean_signature_drift", 0.0))
                if verdict == "M_MINUS" or drift > 0.50:
                    findings.append(RegressionFinding(
                        source="baseline_comparison.json",
                        severity="medium",
                        title=f"[Baseline Drift] {name} unstable under {row.get('noise')} noise σ={row.get('sigma')}",
                        evidence={"benchmark": name, "row": row},
                        suggested_action="Check FFWT signature stability and decide whether this drift belongs in M_MINUS or needs robustification.",
                    ))
    else:
        for benchmark, payload in report.items():
            if not isinstance(payload, dict):
                continue
            errors = payload.get("oak_errors", {})
            for key, value in errors.items():
                if float(value) > 0.20:
                    findings.append(RegressionFinding(
                        source="baseline_comparison.json",
                        severity="medium",
                        title=f"[Baseline Error] {benchmark} {key}={float(value):.4f}",
                        evidence={"benchmark": benchmark, "errors": errors},
                        suggested_action="Compare the OAK estimator against baseline drift and decide whether thresholds need adjustment.",
                    ))
    return findings


def deterministic_diagnosis(findings: List[RegressionFinding]) -> Dict[str, Any]:
    if not findings:
        return {
            "action": "none",
            "oak_verdict": "CANON",
            "issue_title": None,
            "issue_body": None,
            "confidence": 1.0,
            "rationale": "No regressions detected in available OAK reports.",
        }

    highest = findings[0]
    severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    for item in findings[1:]:
        if severity_order.get(item.severity, 0) > severity_order.get(highest.severity, 0):
            highest = item

    body = render_issue_body(findings, llm_note=None)
    return {
        "action": "create_issue",
        "oak_verdict": "M_MINUS" if highest.severity == "critical" else "FERTILE",
        "issue_title": highest.title,
        "issue_body": body,
        "confidence": 0.85,
        "rationale": "Deterministic SAGE fallback selected the highest-severity regression.",
    }


def build_llm_prompt(context: Dict[str, Any], findings: List[RegressionFinding]) -> str:
    return textwrap.dedent(f"""
    You are SAGE, a guarded repository orchestrator for TTM-TFUGA-AI7-TRISTAN2.

    Rules:
    - Output strict JSON only.
    - Do not propose direct source-code rewriting unless the action is issue-only.
    - Allowed actions: none, create_issue.
    - Preserve OAK discipline: CANON requires tests; M_MINUS stores failures.

    Required JSON schema:
    {{
      "action": "none|create_issue",
      "oak_verdict": "CANON|FERTILE|M_MINUS",
      "issue_title": "string|null",
      "issue_body": "string|null",
      "confidence": 0.0,
      "rationale": "string"
    }}

    Context:
    {json.dumps(context, indent=2, ensure_ascii=False, sort_keys=True)[:24000]}

    Findings:
    {json.dumps([asdict(f) for f in findings], indent=2, ensure_ascii=False, sort_keys=True)[:24000]}
    """).strip()


def call_optional_llm(prompt: str) -> Optional[Dict[str, Any]]:
    endpoint = os.environ.get("SAGE_LLM_ENDPOINT")
    api_key = os.environ.get("SAGE_LLM_API_KEY")
    model = os.environ.get("SAGE_LLM_MODEL", "sage-default")
    if not endpoint or not api_key:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"_llm_error": str(exc)}

    try:
        parsed = json.loads(raw)
        # Generic extraction: either raw schema, OpenAI-like choices, or text field.
        if isinstance(parsed, dict) and "action" in parsed:
            return parsed
        content = None
        if isinstance(parsed, dict):
            choices = parsed.get("choices")
            if choices:
                content = choices[0].get("message", {}).get("content") or choices[0].get("text")
            content = content or parsed.get("content") or parsed.get("text")
        if content:
            return json.loads(str(content))
        return {"_llm_error": "Could not extract strict JSON from endpoint response", "raw": parsed}
    except Exception as exc:
        return {"_llm_error": str(exc), "raw": raw[:4000]}


def sanitize_decision(decision: Dict[str, Any], findings: List[RegressionFinding]) -> Dict[str, Any]:
    allowed_actions = {"none", "create_issue"}
    action = decision.get("action")
    if action not in allowed_actions:
        decision["action"] = "create_issue" if findings else "none"
    if findings and decision.get("action") == "none":
        # A missing action is allowed only if the rationale explicitly says all findings are informational.
        rationale = str(decision.get("rationale", "")).lower()
        if "informational" not in rationale and "no action" not in rationale:
            fallback = deterministic_diagnosis(findings)
            fallback["rationale"] += " LLM decision was sanitized."
            return fallback
    return decision


def render_issue_body(findings: List[RegressionFinding], llm_note: Optional[str]) -> str:
    lines = ["# SAGE OAK Diagnostic", ""]
    if llm_note:
        lines += ["## SAGE rationale", "", llm_note, ""]
    lines += ["## Findings", ""]
    for idx, finding in enumerate(findings, 1):
        lines += [
            f"### {idx}. {finding.title}",
            "",
            f"- Source: `{finding.source}`",
            f"- Severity: `{finding.severity}`",
            f"- Suggested action: {finding.suggested_action}",
            "",
            "```json",
            json.dumps(finding.evidence, indent=2, ensure_ascii=False, sort_keys=True),
            "```",
            "",
        ]
    lines += [
        "## Guardrail",
        "",
        "This issue was generated by guarded SAGE orchestration. It proposes diagnosis only and does not modify source code.",
    ]
    return "\n".join(lines)


def github_create_issue(repo: str, token: str, title: str, body: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = json.dumps({"title": title, "body": body, "labels": ["OAK", "SAGE", "regression"]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Guarded SAGE OAK orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Write report only; never create issues")
    parser.add_argument("--create-issue", action="store_true", help="Create a GitHub Issue when a regression is detected")
    args = parser.parse_args(argv)

    oak = read_json(OAK_REPORT)
    auto = read_json(AUTO_GENESIS_REPORT)
    baseline = read_json(BASELINE_REPORT)
    m_minus = read_json(M_MINUS_REGISTRY)

    context = {
        "oak_report": oak,
        "auto_genesis_report": auto,
        "baseline_report": baseline,
        "m_minus_registry": m_minus,
    }
    findings = []
    findings.extend(detect_oak_regressions(oak))
    findings.extend(detect_baseline_regressions(baseline))

    prompt = build_llm_prompt(context, findings)
    llm_decision = call_optional_llm(prompt)
    if llm_decision is None or llm_decision.get("_llm_error"):
        decision = deterministic_diagnosis(findings)
        if llm_decision and llm_decision.get("_llm_error"):
            decision["llm_error"] = llm_decision["_llm_error"]
    else:
        decision = sanitize_decision(llm_decision, findings)
        if decision.get("action") == "create_issue" and not decision.get("issue_body"):
            decision["issue_body"] = render_issue_body(findings, decision.get("rationale"))

    issue_result = None
    if args.create_issue and decision.get("action") == "create_issue":
        repo = os.environ.get("GITHUB_REPOSITORY")
        token = os.environ.get("GITHUB_TOKEN")
        if not repo or not token:
            print("Missing GITHUB_REPOSITORY or GITHUB_TOKEN for issue creation", file=sys.stderr)
            return 2
        issue_result = github_create_issue(repo, token, str(decision["issue_title"]), str(decision["issue_body"]))
    elif not args.dry_run and not args.create_issue:
        print("No action flag supplied; defaulting to dry-run.")

    SAGE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "findings": [asdict(f) for f in findings],
        "decision": decision,
        "issue_result": issue_result,
        "dry_run": not args.create_issue,
    }
    SAGE_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))

    # Nonzero only for actual orchestration infrastructure errors, not for detected regressions.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
