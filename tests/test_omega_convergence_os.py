from omega_convergence_os import (
    BranchDNA,
    Conflict,
    ConflictKind,
    FileChange,
    Severity,
    analyze_python_api,
    analyze_script_conflicts,
    analyze_status_conflicts,
    analyze_workflow_permissions,
    build_branch_dna,
    build_merge_plan,
    compare_branch_dna,
)


def test_branch_dna_digest_is_order_independent():
    common = dict(branch="feature/x", base_sha="a" * 40, head_sha="b" * 40)
    left = BranchDNA(
        **common,
        files=(FileChange("b.py", "modified", "2"), FileChange("a.py", "modified", "1")),
        scripts={"z": "z:main", "a": "a:main"},
    )
    right = BranchDNA(
        **common,
        files=(FileChange("a.py", "modified", "1"), FileChange("b.py", "modified", "2")),
        scripts={"a": "a:main", "z": "z:main"},
    )
    assert left.digest() == right.digest()


def test_python_api_detects_removed_symbol():
    conflicts = analyze_python_api("module.py", "def public(x):\n    return x\n", "VALUE = 1\n")
    assert conflicts[0].severity is Severity.HIGH
    assert conflicts[0].recommended_action == "preserve_or_version_api"


def test_python_api_detects_signature_change():
    conflicts = analyze_python_api(
        "module.py", "def public(x):\n    return x\n", "def public(x, y=1):\n    return x+y\n"
    )
    assert len(conflicts) == 1
    assert conflicts[0].severity is Severity.MEDIUM


def test_script_conflict_is_high():
    base = '[project.scripts]\nomega = "one.cli:main"\n'
    head = '[project.scripts]\nomega = "two.cli:main"\n'
    conflicts = analyze_script_conflicts(base, head)
    assert conflicts[0].kind is ConflictKind.API
    assert conflicts[0].severity is Severity.HIGH


def test_missing_script_is_preserved():
    base = '[project.scripts]\nomega = "one.cli:main"\n'
    head = '[project.scripts]\nother = "two.cli:main"\n'
    conflicts = analyze_script_conflicts(base, head)
    assert any(item.key == "script:omega" for item in conflicts)


def test_workflow_write_escalation_is_critical():
    base = "permissions:\n  contents: read\n"
    head = "permissions:\n  contents: write\n"
    conflicts = analyze_workflow_permissions(".github/workflows/x.yml", base, head)
    assert conflicts[0].severity is Severity.CRITICAL


def test_status_promotion_requires_evidence():
    conflicts = analyze_status_conflicts(
        "theory.md", "status: hypothesis\n", "status: empirical\n"
    )
    assert conflicts[0].kind is ConflictKind.EPISTEMIC
    assert conflicts[0].severity is Severity.HIGH


def test_branch_builder_finds_cli_and_workflow_permissions():
    dna = build_branch_dna(
        branch="feature/x",
        base_sha="a" * 40,
        head_sha="b" * 40,
        file_contents={
            "pyproject.toml": '[project.scripts]\nomega-x = "pkg.cli:main"\n',
            ".github/workflows/x.yml": "permissions:\n  contents: read\n",
            "pkg/api.py": "def run(value):\n    return value\n",
        },
    )
    assert dna.scripts["omega-x"] == "pkg.cli:main"
    assert any(value == "read" for value in dna.workflow_permissions.values())
    assert dna.public_symbols["pkg/api.py"] == ("run",)


def test_compare_binary_requires_sha_preservation():
    base = BranchDNA(
        branch="base", base_sha="a" * 40, head_sha="b" * 40,
        files=(FileChange("data.sqlite3", "modified", "111", binary=True),),
    )
    head = BranchDNA(
        branch="head", base_sha="a" * 40, head_sha="c" * 40,
        files=(FileChange("data.sqlite3", "modified", "222", binary=True),),
    )
    conflict = compare_branch_dna(base, head)[0]
    assert conflict.kind is ConflictKind.BINARY
    assert conflict.recommended_action == "preserve_blob_and_review"


def test_policy_conflict_blocks_plan():
    conflict = Conflict(
        kind=ConflictKind.POLICY,
        severity=Severity.CRITICAL,
        key="workflow:contents",
        message="write escalation",
    )
    plan = build_merge_plan(
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=[".github/workflows/x.yml"],
        conflicts=[conflict],
    )
    assert plan.verdict == "BLOCKED_SECURITY_OR_POLICY"
    assert "workflow_permission_audit" in plan.required_tests
    assert plan.automatic_merge_allowed is False


def test_additive_plan_remains_dry_run_only():
    plan = build_merge_plan(
        base_sha="a" * 40,
        head_sha="b" * 40,
        changed_paths=["new_module.py"],
        conflicts=[],
    )
    assert plan.verdict == "ADDITIVE_DRY_RUN_CANDIDATE"
    assert plan.strategy_by_path["new_module.py"] == "additive_overlay"
    assert plan.automatic_merge_allowed is False
