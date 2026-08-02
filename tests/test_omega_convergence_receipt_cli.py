import json

from omega_convergence_os.cli import main
from omega_convergence_os.models import BranchDNA, Conflict, ConflictKind, Severity
from omega_convergence_os.planner import build_merge_plan
from omega_convergence_os.receipt import build_merge_receipt


def _dna():
    return BranchDNA(
        branch="feature/x",
        base_sha="a" * 40,
        head_sha="b" * 40,
        tests=("python_compile",),
    )


def test_receipt_is_deterministic_with_fixed_timestamp():
    dna = _dna()
    plan = build_merge_plan(
        base_sha=dna.base_sha,
        head_sha=dna.head_sha,
        changed_paths=["x.py"],
        conflicts=[],
    )
    first = build_merge_receipt(branch_dna=dna, plan=plan, timestamp="2026-08-02T20:00:00+00:00")
    second = build_merge_receipt(branch_dna=dna, plan=plan, timestamp="2026-08-02T20:00:00+00:00")
    assert first.receipt_id == second.receipt_id
    assert first.digest() == second.digest()
    assert first.oak_verdict == "DRY_RUN_ONLY"


def test_receipt_records_missing_tests_after_merge():
    dna = _dna()
    conflict = Conflict(
        kind=ConflictKind.API,
        severity=Severity.MEDIUM,
        key="x.py:run",
        message="signature changed",
    )
    plan = build_merge_plan(
        base_sha=dna.base_sha,
        head_sha=dna.head_sha,
        changed_paths=["x.py"],
        conflicts=[conflict],
    )
    receipt = build_merge_receipt(
        branch_dna=dna,
        plan=plan,
        result_sha="c" * 40,
        completed_tests=("python_compile",),
        timestamp="2026-08-02T20:00:00+00:00",
    )
    assert receipt.oak_verdict == "MERGED_TEST_EVIDENCE_INCOMPLETE"
    assert any(item.startswith("missing-tests:") for item in receipt.known_residues)


def test_branch_dna_cli(tmp_path):
    source = tmp_path / "input.json"
    output = tmp_path / "dna.json"
    source.write_text(
        json.dumps(
            {
                "branch": "feature/x",
                "base_sha": "a" * 40,
                "head_sha": "b" * 40,
                "file_contents": {"pkg/api.py": "def run(x):\n    return x\n"},
                "tests": ["unit"],
            }
        ),
        encoding="utf-8",
    )
    assert main(["branch-dna", str(source), "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["branch"] == "feature/x"
    assert len(payload["sha256"]) == 64


def test_plan_cli_blocks_critical_policy(tmp_path):
    source = tmp_path / "input.json"
    output = tmp_path / "plan.json"
    source.write_text(
        json.dumps(
            {
                "base_sha": "a" * 40,
                "head_sha": "b" * 40,
                "changed_paths": [".github/workflows/x.yml"],
                "conflicts": [
                    {
                        "kind": "policy",
                        "severity": "critical",
                        "key": ".github/workflows/x.yml:contents",
                        "message": "write escalation",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["plan", str(source), "--output", str(output)]) == 2
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["verdict"] == "BLOCKED_SECURITY_OR_POLICY"
    assert payload["automatic_merge_allowed"] is False


def test_receipt_cli_never_promotes_or_merges(tmp_path):
    source = tmp_path / "input.json"
    output = tmp_path / "receipt.json"
    source.write_text(
        json.dumps(
            {
                "branch_dna": _dna().canonical_dict(),
                "plan": {
                    "base_sha": "a" * 40,
                    "head_sha": "b" * 40,
                    "strategy_by_path": {"x.py": "additive_overlay"},
                    "conflicts": [],
                    "required_tests": ["python_compile"],
                    "preservation_paths": [],
                    "rollback_steps": ["revert"],
                    "verdict": "ADDITIVE_DRY_RUN_CANDIDATE",
                },
                "completed_tests": ["python_compile"],
                "timestamp": "2026-08-02T20:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    assert main(["receipt", str(source), "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["automatic_merge"] is False
    assert payload["automatic_scientific_promotion"] is False
