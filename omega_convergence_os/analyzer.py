from __future__ import annotations

import ast
import hashlib
import re
from typing import Iterable, Mapping, Sequence

from .models import BranchDNA, Conflict, ConflictKind, FileChange, Severity


_PERMISSION_ORDER = {"none": 0, "read": 1, "write": 2}
_STATUS_ORDER = {
    "idea": 0,
    "hypothesis": 1,
    "prototype": 2,
    "tested": 3,
    "validated_synthetic": 4,
    "empirical": 5,
    "replicated": 6,
    "canon": 7,
}
_BINARY_SUFFIXES = {
    ".7z", ".avi", ".bin", ".bmp", ".db", ".gif", ".gz", ".ico", ".jpeg",
    ".jpg", ".mp3", ".mp4", ".parquet", ".pdf", ".png", ".sqlite", ".sqlite3",
    ".tar", ".webp", ".zip", ".zst",
}


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_binary_path(path: str) -> bool:
    lowered = path.lower()
    return any(lowered.endswith(suffix) for suffix in _BINARY_SUFFIXES)


def extract_public_python_symbols(content: str) -> dict[str, str]:
    """Return public top-level symbol signatures without importing the code."""
    tree = ast.parse(content)
    symbols: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            positional = [arg.arg for arg in (*node.args.posonlyargs, *node.args.args)]
            defaults_start = len(positional) - len(node.args.defaults)
            rendered: list[str] = []
            for index, name in enumerate(positional):
                suffix = "=" if index >= defaults_start else ""
                rendered.append(name + suffix)
            if node.args.vararg:
                rendered.append("*" + node.args.vararg.arg)
            elif node.args.kwonlyargs:
                rendered.append("*")
            rendered.extend(
                arg.arg + ("=" if default is not None else "")
                for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults)
            )
            if node.args.kwarg:
                rendered.append("**" + node.args.kwarg.arg)
            prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            symbols[node.name] = f"{prefix}({','.join(rendered)})"
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            bases = [ast.unparse(base) for base in node.bases]
            symbols[node.name] = f"class({','.join(bases)})"
    return symbols


def analyze_python_api(path: str, base_content: str, head_content: str) -> tuple[Conflict, ...]:
    try:
        base = extract_public_python_symbols(base_content)
        head = extract_public_python_symbols(head_content)
    except SyntaxError as exc:
        return (
            Conflict(
                kind=ConflictKind.API,
                severity=Severity.CRITICAL,
                key=path,
                message=f"Python syntax prevents API analysis: {exc.msg}",
                recommended_action="repair_syntax_before_merge",
            ),
        )

    conflicts: list[Conflict] = []
    for name in sorted(set(base) - set(head)):
        conflicts.append(
            Conflict(
                kind=ConflictKind.API,
                severity=Severity.HIGH,
                key=f"{path}:{name}",
                message="Public symbol removed",
                base_value=base[name],
                head_value=None,
                recommended_action="preserve_or_version_api",
            )
        )
    for name in sorted(set(base) & set(head)):
        if base[name] != head[name]:
            conflicts.append(
                Conflict(
                    kind=ConflictKind.API,
                    severity=Severity.MEDIUM,
                    key=f"{path}:{name}",
                    message="Public symbol signature changed",
                    base_value=base[name],
                    head_value=head[name],
                    recommended_action="add_adapter_or_migration_test",
                )
            )
    return tuple(conflicts)


def extract_project_scripts(content: str) -> dict[str, str]:
    scripts: dict[str, str] = {}
    in_scripts = False
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_scripts = line == "[project.scripts]"
            continue
        if not in_scripts or not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        scripts[key.strip()] = value.strip().strip('"').strip("'")
    return scripts


def analyze_script_conflicts(base_content: str, head_content: str) -> tuple[Conflict, ...]:
    base = extract_project_scripts(base_content)
    head = extract_project_scripts(head_content)
    conflicts: list[Conflict] = []
    for name in sorted(set(base) & set(head)):
        if base[name] != head[name]:
            conflicts.append(
                Conflict(
                    kind=ConflictKind.API,
                    severity=Severity.HIGH,
                    key=f"script:{name}",
                    message="CLI entry point targets differ",
                    base_value=base[name],
                    head_value=head[name],
                    recommended_action="rename_or_select_single_entrypoint",
                )
            )
    for name in sorted(set(base) - set(head)):
        conflicts.append(
            Conflict(
                kind=ConflictKind.API,
                severity=Severity.MEDIUM,
                key=f"script:{name}",
                message="Existing CLI entry point would disappear",
                base_value=base[name],
                recommended_action="preserve_existing_cli",
            )
        )
    return tuple(conflicts)


def extract_workflow_permissions(content: str) -> dict[str, str]:
    """Parse the simple permissions forms used by GitHub Actions without YAML deps."""
    permissions: dict[str, str] = {}
    lines = content.splitlines()
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("permissions:"):
            remainder = stripped.partition(":")[2].strip()
            if remainder in {"read-all", "write-all"}:
                permissions["*"] = "read" if remainder == "read-all" else "write"
                continue
            parent_indent = len(raw) - len(raw.lstrip())
            for child in lines[index + 1 :]:
                if not child.strip() or child.lstrip().startswith("#"):
                    continue
                indent = len(child) - len(child.lstrip())
                if indent <= parent_indent:
                    break
                match = re.match(r"\s*([A-Za-z0-9_-]+)\s*:\s*(read|write|none)\s*$", child)
                if match:
                    permissions[match.group(1)] = match.group(2)
    return permissions


def analyze_workflow_permissions(path: str, base_content: str, head_content: str) -> tuple[Conflict, ...]:
    base = extract_workflow_permissions(base_content)
    head = extract_workflow_permissions(head_content)
    conflicts: list[Conflict] = []
    for scope in sorted(set(base) | set(head)):
        before = base.get(scope, "none")
        after = head.get(scope, "none")
        if _PERMISSION_ORDER.get(after, 0) > _PERMISSION_ORDER.get(before, 0):
            severity = Severity.CRITICAL if scope in {"contents", "pull-requests", "actions", "id-token"} and after == "write" else Severity.HIGH
            conflicts.append(
                Conflict(
                    kind=ConflictKind.POLICY,
                    severity=severity,
                    key=f"{path}:permissions:{scope}",
                    message="Workflow permission escalation",
                    base_value=before,
                    head_value=after,
                    recommended_action="require_human_security_review",
                )
            )
    return tuple(conflicts)


def extract_epistemic_statuses(content: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    patterns = [
        r"(?im)^\s*(?:status|statut|epistemic_status)\s*[:=]\s*[\"']?([a-zA-Z_-]+)",
        r"(?im)^\s*[-*]\s*(?:status|statut)\s*:\s*`?([a-zA-Z_-]+)`?",
    ]
    for pattern in patterns:
        for index, match in enumerate(re.finditer(pattern, content)):
            value = match.group(1).lower().replace("-", "_")
            statuses[f"status_{match.start()}_{index}"] = value
    return statuses


def analyze_status_conflicts(path: str, base_content: str, head_content: str) -> tuple[Conflict, ...]:
    base_values = list(extract_epistemic_statuses(base_content).values())
    head_values = list(extract_epistemic_statuses(head_content).values())
    if not base_values or not head_values:
        return ()
    before = max(base_values, key=lambda item: _STATUS_ORDER.get(item, -1))
    after = max(head_values, key=lambda item: _STATUS_ORDER.get(item, -1))
    if _STATUS_ORDER.get(after, -1) <= _STATUS_ORDER.get(before, -1):
        return ()
    return (
        Conflict(
            kind=ConflictKind.EPISTEMIC,
            severity=Severity.HIGH if _STATUS_ORDER.get(after, 0) >= 5 else Severity.MEDIUM,
            key=f"{path}:status",
            message="Epistemic status strengthened",
            base_value=before,
            head_value=after,
            recommended_action="require_evidence_for_status_promotion",
        ),
    )


def build_branch_dna(
    *,
    branch: str,
    base_sha: str,
    head_sha: str,
    file_contents: Mapping[str, str],
    statuses: Mapping[str, str] | None = None,
    tests: Sequence[str] = (),
    claims: Sequence[str] = (),
    risks: Sequence[str] = (),
) -> BranchDNA:
    files: list[FileChange] = []
    public_symbols: dict[str, tuple[str, ...]] = {}
    scripts: dict[str, str] = {}
    permissions: dict[str, str] = {}
    epistemic_statuses: dict[str, str] = dict(statuses or {})

    for path, content in sorted(file_contents.items()):
        binary = _is_binary_path(path)
        files.append(
            FileChange(
                path=path,
                status="modified",
                sha256=_sha256_text(content),
                size_bytes=len(content.encode("utf-8")),
                binary=binary,
            )
        )
        if path.endswith(".py") and not binary:
            try:
                public_symbols[path] = tuple(sorted(extract_public_python_symbols(content)))
            except SyntaxError:
                risks = (*risks, f"syntax-error:{path}")
        if path.endswith("pyproject.toml"):
            scripts.update(extract_project_scripts(content))
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            for key, value in extract_workflow_permissions(content).items():
                permissions[f"{path}:{key}"] = value
        if path.endswith((".md", ".json", ".yaml", ".yml")):
            for key, value in extract_epistemic_statuses(content).items():
                epistemic_statuses[f"{path}:{key}"] = value

    return BranchDNA(
        branch=branch,
        base_sha=base_sha,
        head_sha=head_sha,
        files=tuple(files),
        public_symbols=public_symbols,
        scripts=scripts,
        workflow_permissions=permissions,
        epistemic_statuses=epistemic_statuses,
        claims=tuple(claims),
        tests=tuple(tests),
        risks=tuple(risks),
    )


def compare_branch_dna(base: BranchDNA, head: BranchDNA) -> tuple[Conflict, ...]:
    conflicts: list[Conflict] = []
    base_files = {item.path: item for item in base.files}
    head_files = {item.path: item for item in head.files}
    for path in sorted(set(base_files) & set(head_files)):
        left, right = base_files[path], head_files[path]
        if left.sha256 != right.sha256:
            kind = ConflictKind.BINARY if left.binary or right.binary else ConflictKind.FILE
            severity = Severity.HIGH if kind is ConflictKind.BINARY else Severity.MEDIUM
            conflicts.append(
                Conflict(
                    kind=kind,
                    severity=severity,
                    key=path,
                    message="Both branch states contain different content for the same path",
                    base_value=left.sha256,
                    head_value=right.sha256,
                    recommended_action="preserve_blob_and_review" if kind is ConflictKind.BINARY else "semantic_merge",
                )
            )

    for script in sorted(set(base.scripts) & set(head.scripts)):
        if base.scripts[script] != head.scripts[script]:
            conflicts.append(
                Conflict(
                    kind=ConflictKind.API,
                    severity=Severity.HIGH,
                    key=f"script:{script}",
                    message="Branch DNA exposes different targets for one CLI name",
                    base_value=base.scripts[script],
                    head_value=head.scripts[script],
                    recommended_action="rename_or_reconcile_cli",
                )
            )

    for permission in sorted(set(base.workflow_permissions) | set(head.workflow_permissions)):
        before = base.workflow_permissions.get(permission, "none")
        after = head.workflow_permissions.get(permission, "none")
        if _PERMISSION_ORDER.get(after, 0) > _PERMISSION_ORDER.get(before, 0):
            conflicts.append(
                Conflict(
                    kind=ConflictKind.POLICY,
                    severity=Severity.CRITICAL if after == "write" else Severity.HIGH,
                    key=permission,
                    message="Branch DNA increases workflow authority",
                    base_value=before,
                    head_value=after,
                    recommended_action="security_review",
                )
            )
    return tuple(conflicts)
