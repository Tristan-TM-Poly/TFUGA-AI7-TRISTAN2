"""Static, read-only optimizer for GitHub Actions workflows.

Ω-ACTIONS-T∞ turns workflow YAML into a structural execution graph and emits
measurable optimization hypotheses. The analyzer is intentionally stdlib-only:
it does not execute YAML, call GitHub, modify workflows, or require network
access. Findings are static proxies until validated against real run telemetry.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

_WORKFLOW_SUFFIXES = {".yml", ".yaml"}
_JOB_KEY = re.compile(r"^ {2}([A-Za-z0-9_.-]+):\s*(?:#.*)?$")
_KEY_VALUE = re.compile(r"^\s*([A-Za-z0-9_.-]+):\s*(.*?)\s*$")
_NEEDS_INLINE = re.compile(r"\[(.*?)\]")
_RUNNER_EXPR = re.compile(r"runs-on:\s*(.+)$")
_TIMEOUT = re.compile(r"timeout-minutes:\s*(\d+)")
_MAX_PARALLEL = re.compile(r"max-parallel:\s*(\d+)")


@dataclass
class JobMetrics:
    name: str
    needs: list[str] = field(default_factory=list)
    runner: str | None = None
    timeout_minutes: int | None = None
    uses_actions: list[str] = field(default_factory=list)
    run_commands: list[str] = field(default_factory=list)
    cache_uses: int = 0
    upload_artifacts: int = 0
    download_artifacts: int = 0
    install_steps: int = 0


@dataclass
class WorkflowMetrics:
    path: str
    name: str
    triggers: list[str]
    jobs: list[JobMetrics]
    has_concurrency: bool
    has_permissions: bool
    path_filter_entries: int
    matrix_axes: int
    max_parallel: int | None
    behavior_signature: str
    behavior_tokens: list[str]
    structural_depth: int
    recommendations: list[dict[str, Any]]


def _strip_comment(line: str) -> str:
    if "#" not in line:
        return line.rstrip()
    match = re.search(r"\s+#", line)
    return line[: match.start()].rstrip() if match else line.rstrip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_command(command: str) -> str:
    command = re.sub(r"\s+", " ", command.strip())
    command = re.sub(r"\b\d+(?:\.\d+){0,3}\b", "<N>", command)
    return command[:240]


def _parse_needs(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    match = _NEEDS_INLINE.search(value)
    if match:
        return [item.strip().strip("'\"") for item in match.group(1).split(",") if item.strip()]
    return [value.strip("'\"")]


def _extract_triggers(lines: list[str]) -> list[str]:
    triggers: list[str] = []
    on_index: int | None = None
    for index, raw in enumerate(lines):
        line = _strip_comment(raw)
        if line.startswith("on:") and _indent(line) == 0:
            on_index = index
            inline = line.partition(":")[2].strip()
            if inline:
                if inline.startswith("[") and inline.endswith("]"):
                    triggers.extend(item.strip().strip("'\"") for item in inline[1:-1].split(",") if item.strip())
                else:
                    triggers.append(inline.strip("'\""))
            break
    if on_index is None:
        return triggers
    for raw in lines[on_index + 1 :]:
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = _indent(line)
        if indent == 0:
            break
        if indent == 2:
            match = _KEY_VALUE.match(line)
            if match:
                triggers.append(match.group(1))
    return sorted(set(triggers))


def _extract_path_filter_entries(lines: list[str]) -> int:
    count = 0
    active_indent: int | None = None
    for raw in lines:
        line = _strip_comment(raw)
        stripped = line.strip()
        indent = _indent(line)
        if stripped in {"paths:", "paths-ignore:"}:
            active_indent = indent
            continue
        if active_indent is not None:
            if stripped.startswith("- ") and indent > active_indent:
                count += 1
                continue
            if stripped and indent <= active_indent:
                active_indent = None
    return count


def _extract_matrix_axes(lines: list[str]) -> int:
    axes = 0
    matrix_indent: int | None = None
    for raw in lines:
        line = _strip_comment(raw)
        stripped = line.strip()
        indent = _indent(line)
        if stripped == "matrix:":
            matrix_indent = indent
            continue
        if matrix_indent is not None:
            if stripped and indent <= matrix_indent:
                matrix_indent = None
                continue
            if indent == matrix_indent + 2 and stripped and not stripped.startswith(("-", "include:", "exclude:")):
                match = _KEY_VALUE.match(line)
                if match and match.group(1) not in {"include", "exclude"}:
                    axes += 1
    return axes


def _job_sections(lines: list[str]) -> dict[str, list[str]]:
    jobs_index: int | None = None
    for index, raw in enumerate(lines):
        line = _strip_comment(raw)
        if line.strip() == "jobs:" and _indent(line) == 0:
            jobs_index = index
            break
    if jobs_index is None:
        return {}

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in lines[jobs_index + 1 :]:
        line = _strip_comment(raw)
        if not line.strip():
            if current:
                sections[current].append(raw)
            continue
        indent = _indent(line)
        if indent == 0:
            break
        match = _JOB_KEY.match(line)
        if match:
            current = match.group(1)
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw)
    return sections


def _parse_job(name: str, lines: list[str]) -> JobMetrics:
    job = JobMetrics(name=name)
    block_needs = False
    needs_indent: int | None = None
    for raw in lines:
        line = _strip_comment(raw)
        stripped = line.strip()
        indent = _indent(line)
        if not stripped:
            continue

        if stripped.startswith("needs:"):
            value = stripped.partition(":")[2].strip()
            if value:
                job.needs.extend(_parse_needs(value))
                block_needs = False
            else:
                block_needs = True
                needs_indent = indent
            continue
        if block_needs:
            if stripped.startswith("- ") and needs_indent is not None and indent > needs_indent:
                job.needs.append(stripped[2:].strip().strip("'\""))
                continue
            if needs_indent is not None and indent <= needs_indent:
                block_needs = False

        match = _RUNNER_EXPR.search(stripped)
        if match:
            job.runner = match.group(1).strip().strip("'\"")
        match = _TIMEOUT.search(stripped)
        if match:
            job.timeout_minutes = int(match.group(1))

        if stripped.startswith("uses:"):
            action = stripped.partition(":")[2].strip().strip("'\"")
            job.uses_actions.append(action)
            lowered = action.lower()
            job.cache_uses += int("actions/cache@" in lowered)
            job.upload_artifacts += int("upload-artifact@" in lowered)
            job.download_artifacts += int("download-artifact@" in lowered)

        lowered = stripped.lower()
        if stripped.startswith("run:"):
            command = stripped.partition(":")[2].strip()
            if command and command not in {"|", ">"}:
                job.run_commands.append(_normalize_command(command))
        if any(token in lowered for token in ("pip install", "npm ci", "npm install", "pnpm install", "yarn install", "cargo fetch")):
            job.install_steps += 1
        if stripped.startswith("cache:"):
            job.cache_uses += 1

    job.needs = sorted(set(job.needs))
    return job


def _structural_depth(jobs: list[JobMetrics]) -> int:
    if not jobs:
        return 0
    by_name = {job.name: job for job in jobs}
    memo: dict[str, int] = {}

    def depth(name: str, visiting: set[str]) -> int:
        if name in memo:
            return memo[name]
        if name in visiting:
            return 1
        job = by_name[name]
        deps = [dep for dep in job.needs if dep in by_name]
        memo[name] = 1 if not deps else 1 + max(depth(dep, visiting | {name}) for dep in deps)
        return memo[name]

    return max(depth(name, set()) for name in by_name)


def _behavior_tokens(jobs: list[JobMetrics]) -> list[str]:
    tokens: set[str] = set()
    for job in jobs:
        if job.runner:
            tokens.add(f"runner:{job.runner}")
        for action in job.uses_actions:
            tokens.add("uses:" + action.split("@", 1)[0].lower())
        for command in job.run_commands:
            head = command.split(" ", 1)[0].lower()
            tokens.add("run:" + head)
        if job.cache_uses:
            tokens.add("feature:cache")
        if job.upload_artifacts or job.download_artifacts:
            tokens.add("feature:artifacts")
    return sorted(tokens)


def _recommendations(*, triggers: list[str], jobs: list[JobMetrics], has_concurrency: bool,
                     has_permissions: bool, matrix_axes: int, max_parallel: int | None,
                     path_filter_entries: int) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    install_steps = sum(job.install_steps for job in jobs)
    cache_uses = sum(job.cache_uses for job in jobs)
    uploads = sum(job.upload_artifacts for job in jobs)
    downloads = sum(job.download_artifacts for job in jobs)
    missing_timeouts = sum(job.timeout_minutes is None for job in jobs)

    if {"pull_request", "push"} & set(triggers) and not has_concurrency:
        recommendations.append({"id": "cancel-obsolete-runs", "priority": 0.95,
            "evidence": "push/pull_request trigger without concurrency",
            "proposal": "Add concurrency keyed by workflow/ref and cancel-in-progress for superseded runs."})
    if install_steps and not cache_uses:
        recommendations.append({"id": "cache-installation-work", "priority": 0.90,
            "evidence": f"{install_steps} dependency-install step(s) and no detected cache",
            "proposal": "Measure dependency cache restore/save time and enable cache only when net value is positive."})
    if missing_timeouts:
        recommendations.append({"id": "bound-job-runtime", "priority": 0.78,
            "evidence": f"{missing_timeouts}/{len(jobs)} job(s) without timeout-minutes",
            "proposal": "Set evidence-based timeout-minutes to cap hung or pathological jobs."})
    if matrix_axes and max_parallel is None:
        recommendations.append({"id": "adaptive-matrix-parallelism", "priority": 0.76,
            "evidence": f"{matrix_axes} matrix axis/axes and no max-parallel",
            "proposal": "Benchmark queue/runner saturation before choosing adaptive max-parallel policy."})
    if uploads + downloads >= 2:
        recommendations.append({"id": "review-artifact-flow", "priority": 0.66,
            "evidence": f"{uploads} upload(s) + {downloads} download(s)",
            "proposal": "Compare transfer/startup overhead with job fusion and direct recomputation."})
    if not has_permissions:
        recommendations.append({"id": "least-privilege-permissions", "priority": 0.88,
            "evidence": "No explicit permissions block detected",
            "proposal": "Declare minimum GITHUB_TOKEN permissions explicitly."})
    if ("pull_request" in triggers or "push" in triggers) and path_filter_entries == 0:
        recommendations.append({"id": "delta-ci-entry-filter", "priority": 0.58,
            "evidence": "Repository-triggered workflow has no path filter",
            "proposal": "Evaluate path filtering or a dynamic impact-analysis job; preserve required-check semantics."})
    return sorted(recommendations, key=lambda item: float(item["priority"]), reverse=True)


def analyze_workflow(path: Path, root: Path | None = None) -> WorkflowMetrics:
    root = root or path.parent
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    jobs = [_parse_job(name, body) for name, body in _job_sections(lines).items()]
    triggers = _extract_triggers(lines)
    name = path.stem
    for raw in lines:
        line = _strip_comment(raw)
        if line.startswith("name:") and _indent(line) == 0:
            name = line.partition(":")[2].strip().strip("'\"") or path.stem
            break

    has_concurrency = any(_indent(_strip_comment(line)) == 0 and _strip_comment(line).strip() == "concurrency:" for line in lines)
    has_permissions = any(_indent(_strip_comment(line)) == 0 and _strip_comment(line).strip().startswith("permissions:") for line in lines)
    path_filter_entries = _extract_path_filter_entries(lines)
    matrix_axes = _extract_matrix_axes(lines)
    max_parallel_values = [int(match.group(1)) for line in lines if (match := _MAX_PARALLEL.search(_strip_comment(line)))]
    max_parallel = max_parallel_values[0] if max_parallel_values else None
    tokens = _behavior_tokens(jobs)
    signature_payload = json.dumps({"tokens": tokens, "jobs": len(jobs), "depth": _structural_depth(jobs), "matrix_axes": matrix_axes}, sort_keys=True).encode("utf-8")
    signature = hashlib.sha256(signature_payload).hexdigest()[:16]

    return WorkflowMetrics(
        path=path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix(),
        name=name,
        triggers=triggers,
        jobs=jobs,
        has_concurrency=has_concurrency,
        has_permissions=has_permissions,
        path_filter_entries=path_filter_entries,
        matrix_axes=matrix_axes,
        max_parallel=max_parallel,
        behavior_signature=signature,
        behavior_tokens=tokens,
        structural_depth=_structural_depth(jobs),
        recommendations=_recommendations(triggers=triggers, jobs=jobs, has_concurrency=has_concurrency,
            has_permissions=has_permissions, matrix_axes=matrix_axes, max_parallel=max_parallel,
            path_filter_entries=path_filter_entries),
    )


def iter_workflows(root: Path) -> Iterable[Path]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return ()
    return tuple(sorted(path for path in workflows.rglob("*") if path.is_file() and path.suffix.lower() in _WORKFLOW_SUFFIXES))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _duplicate_analysis(workflows: list[WorkflowMetrics]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact: dict[str, list[str]] = {}
    for workflow in workflows:
        exact.setdefault(workflow.behavior_signature, []).append(workflow.path)
    exact_groups = [{"signature": signature, "workflows": sorted(paths), "count": len(paths)}
                    for signature, paths in exact.items() if len(paths) > 1]

    near: list[dict[str, Any]] = []
    for index, left in enumerate(workflows):
        left_tokens = set(left.behavior_tokens)
        for right in workflows[index + 1 :]:
            if left.behavior_signature == right.behavior_signature:
                continue
            score = _jaccard(left_tokens, set(right.behavior_tokens))
            if score >= 0.85 and min(len(left_tokens), len(right.behavior_tokens)) >= 2:
                near.append({"left": left.path, "right": right.path, "similarity": round(score, 3)})
    near.sort(key=lambda item: float(item["similarity"]), reverse=True)
    return exact_groups, near[:100]


def _aggregate(workflows: list[WorkflowMetrics], exact_groups: list[dict[str, Any]], near_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    jobs = [job for workflow in workflows for job in workflow.jobs]
    no_concurrency = sum(not workflow.has_concurrency and bool({"push", "pull_request"} & set(workflow.triggers)) for workflow in workflows)
    cache_uses = sum(job.cache_uses for job in jobs)
    install_steps = sum(job.install_steps for job in jobs)
    artifact_transfers = sum(job.upload_artifacts + job.download_artifacts for job in jobs)
    missing_timeouts = sum(job.timeout_minutes is None for job in jobs)
    duplicate_members = sum(group["count"] for group in exact_groups)

    waste_proxy = (no_concurrency * 2 + max(0, install_steps - cache_uses) + artifact_transfers * 0.5
                   + missing_timeouts * 0.25 + duplicate_members + len(near_pairs) * 0.5)
    validation_proxy = len(jobs) + sum(workflow.path_filter_entries > 0 for workflow in workflows) + sum(workflow.matrix_axes for workflow in workflows)
    confidence_proxy = 1.0 if not jobs else 0.5 + 0.5 * (1 - missing_timeouts / len(jobs))
    static_efficiency = 100.0 * (validation_proxy * confidence_proxy) / max(1.0, validation_proxy + waste_proxy)

    return {
        "workflow_count": len(workflows),
        "job_count": len(jobs),
        "max_structural_depth": max((workflow.structural_depth for workflow in workflows), default=0),
        "workflows_without_concurrency": no_concurrency,
        "dependency_install_steps": install_steps,
        "cache_signals": cache_uses,
        "artifact_transfers": artifact_transfers,
        "jobs_without_timeout": missing_timeouts,
        "exact_duplicate_groups": len(exact_groups),
        "near_duplicate_pairs": len(near_pairs),
        "recommendation_count": sum(len(workflow.recommendations) for workflow in workflows),
        "static_efficiency_score": round(static_efficiency, 2),
        "static_efficiency_is_proxy": True,
    }


def analyze_repository(root: str | Path = ".") -> dict[str, Any]:
    root_path = Path(root).resolve()
    workflows = [analyze_workflow(path, root_path) for path in iter_workflows(root_path)]
    exact_groups, near_pairs = _duplicate_analysis(workflows)
    aggregate = _aggregate(workflows, exact_groups, near_pairs)

    repository_recommendations: list[dict[str, Any]] = []
    if exact_groups or near_pairs:
        repository_recommendations.append({"id": "consolidate-workflow-families", "priority": 0.97,
            "evidence": f"{len(exact_groups)} exact duplicate group(s), {len(near_pairs)} near-duplicate pair(s)",
            "proposal": "Extract reusable workflows/composite actions or generate parameterized matrices instead of maintaining repeated YAML."})
    if aggregate["workflow_count"] >= 20:
        repository_recommendations.append({"id": "compile-workflows-from-ci-ir", "priority": 0.92,
            "evidence": f"{aggregate['workflow_count']} workflow files",
            "proposal": "Introduce a declarative CI intermediate representation and generate repetitive workflow families."})

    return {
        "schema": "omega-actions-t.static-analysis.v1",
        "root": str(root_path),
        "aggregate": aggregate,
        "duplicate_groups": exact_groups,
        "near_duplicate_pairs": near_pairs,
        "repository_recommendations": repository_recommendations,
        "workflows": [{**asdict(workflow), "jobs": [asdict(job) for job in workflow.jobs]} for workflow in workflows],
        "oak_limits": [
            "Static analysis is not measured wall-clock telemetry.",
            "Behavior similarity is a heuristic and must not trigger deletion automatically.",
            "No workflow, secret, permission, runner, branch, or GitHub setting is modified.",
            "Optimization claims require before/after run evidence.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    aggregate = report["aggregate"]
    lines = [
        "# Ω-ACTIONS-T∞ — Static GitHub Actions Optimization Report", "",
        f"- Workflows: **{aggregate['workflow_count']}**",
        f"- Jobs: **{aggregate['job_count']}**",
        f"- Structural critical-path depth: **{aggregate['max_structural_depth']}** jobs",
        f"- Workflows lacking concurrency cancellation opportunity: **{aggregate['workflows_without_concurrency']}**",
        f"- Dependency-install signals: **{aggregate['dependency_install_steps']}**",
        f"- Cache signals: **{aggregate['cache_signals']}**",
        f"- Artifact transfers: **{aggregate['artifact_transfers']}**",
        f"- Jobs without timeout: **{aggregate['jobs_without_timeout']}**",
        f"- Exact duplicate groups: **{aggregate['exact_duplicate_groups']}**",
        f"- Near-duplicate pairs: **{aggregate['near_duplicate_pairs']}**",
        f"- Static Action Efficiency proxy: **{aggregate['static_efficiency_score']}/100**", "",
        "> OAK: the score is a structural proxy, not measured CI performance.", "",
        "## Repository-level recommendations", "",
    ]
    if report["repository_recommendations"]:
        for recommendation in report["repository_recommendations"]:
            lines.append(f"- **{recommendation['id']}** ({recommendation['priority']:.2f}) — {recommendation['proposal']} Evidence: {recommendation['evidence']}")
    else:
        lines.append("- No repository-level consolidation recommendation triggered.")

    lines.extend(["", "## Highest-priority workflow findings", ""])
    findings: list[tuple[float, str, dict[str, Any]]] = []
    for workflow in report["workflows"]:
        for recommendation in workflow["recommendations"]:
            findings.append((float(recommendation["priority"]), workflow["path"], recommendation))
    findings.sort(reverse=True, key=lambda item: item[0])
    for priority, path, recommendation in findings[:40]:
        lines.append(f"- `{path}` — **{recommendation['id']}** ({priority:.2f}): {recommendation['evidence']} → {recommendation['proposal']}")
    if not findings:
        lines.append("- No workflow-level findings.")

    lines.extend(["", "## OAK limits", ""])
    for item in report["oak_limits"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_report(root: str | Path = ".", *, json_out: str | Path | None = None,
                 markdown_out: str | Path | None = None) -> dict[str, Any]:
    report = analyze_repository(root)
    if json_out is not None:
        Path(json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if markdown_out is not None:
        Path(markdown_out).write_text(render_markdown(report), encoding="utf-8")
    return report
