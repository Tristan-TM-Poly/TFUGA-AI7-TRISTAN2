from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Iterable

from .models import CostEstimate, ImpactPlan, RepoTwinManifest, sorted_unique
from .scanner import package_for_path, workflow_matches

GLOBAL_FILES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "requirements.txt",
    "requirements-dev.txt",
    "uv.lock",
    "poetry.lock",
}
GLOBAL_PREFIXES = ("shared/", "interfaces/", "policies/", "schemas/shared")


class ImpactRouter:
    """Conservative change router derived from a deterministic repository twin."""

    def route(self, manifest: RepoTwinManifest, changed_paths: Iterable[str]) -> ImpactPlan:
        normalized_paths = []
        for raw_path in changed_paths:
            path = raw_path.strip()
            while path.startswith("./"):
                path = path[2:]
            if path:
                normalized_paths.append(path)
        changed = sorted_unique(tuple(normalized_paths))
        if not changed:
            raise ValueError("at least one changed path is required")
        file_by_path = {record.path: record for record in manifest.files}
        known_packages = {record.package for record in manifest.files}
        reverse_dependencies: dict[str, set[str]] = defaultdict(set)
        for source, target in manifest.dependency_edges:
            reverse_dependencies[target].add(source)

        seeds: set[str] = set()
        unknown: list[str] = []
        reasons: list[str] = []
        for path in changed:
            record = file_by_path.get(path)
            package = record.package if record else package_for_path(path)
            seeds.add(package)
            if record is None:
                unknown.append(path)
            if path in GLOBAL_FILES or path.startswith(GLOBAL_PREFIXES):
                reasons.append(f"global_contract_changed:{path}")
            if path.startswith(".github/workflows/"):
                reasons.append(f"workflow_definition_changed:{path}")

        affected = set(seeds)
        queue = deque(sorted(seeds))
        while queue:
            dependency = queue.popleft()
            for consumer in sorted(reverse_dependencies.get(dependency, ())):
                if consumer not in affected:
                    affected.add(consumer)
                    queue.append(consumer)

        tests: set[str] = set()
        for test_path, imported in manifest.test_edges:
            if imported in affected:
                tests.add(test_path)
        for path in changed:
            if path.startswith("tests/") or Path(path).name.startswith("test_"):
                tests.add(path)
        for record in manifest.files:
            if record.kind == "test" and any(pkg.replace("-", "_") in record.path for pkg in affected):
                tests.add(record.path)

        workflows: set[str] = set()
        for rule in manifest.workflows:
            if any(workflow_matches(rule, path) for path in changed):
                workflows.add(rule.path)

        global_change = any(path in GLOBAL_FILES or path.startswith(GLOBAL_PREFIXES) for path in changed)
        broad_impact = len(affected - {"root", "tests", "docs", "schemas", "examples", ".github"}) > 8
        unknown_risky = any(package_for_path(path) not in known_packages for path in unknown)
        full_suite = global_change or broad_impact or unknown_risky
        if global_change:
            reasons.append("global_configuration_or_contract_requires_repository_integration")
        if broad_impact:
            reasons.append("reverse_dependency_closure_exceeds_eight_packages")
        if unknown_risky:
            reasons.append("unknown_path_outside_known_package_graph")
        if not tests:
            reasons.append("no_direct_test_mapping_found")
        if not workflows:
            reasons.append("no_workflow_path_filter_matched")

        tiers = ["focused"]
        if len(affected) > 1 or workflows or global_change:
            tiers.append("integration")
        if full_suite:
            tiers.append("nightly_or_manual_full")

        focused = max(1, len(tests))
        integration = max(focused, len(affected) * 2) if "integration" in tiers else 0
        workflow_units = len(workflows)
        scan_units = len(manifest.files)
        relative_score = round(focused + integration * 1.5 + workflow_units * 3 + scan_units / 1000, 3)
        cost = CostEstimate(
            focused_test_units=focused,
            integration_test_units=integration,
            workflow_units=workflow_units,
            file_scan_units=scan_units,
            relative_cost_score=relative_score,
        )
        return ImpactPlan(
            changed_paths=changed,
            affected_packages=sorted_unique(tuple(affected)),
            affected_tests=sorted_unique(tuple(tests)),
            selected_workflows=sorted_unique(tuple(workflows)),
            tiers=tuple(tiers),
            reasons=sorted_unique(tuple(reasons)),
            full_suite_required=full_suite,
            unknown_paths=sorted_unique(tuple(unknown)),
            cost=cost,
            manifest_digest=manifest.root_digest,
        )
