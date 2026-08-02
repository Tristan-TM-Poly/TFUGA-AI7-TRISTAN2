from pathlib import Path

import pytest

from omega_mail_github_loop_t.anti_loop import evaluate_mail
from omega_mail_github_loop_t.atlas import EXPECTED_CELLS, EXPECTED_SHARDS, audit, generate
from omega_mail_github_loop_t.authority import evaluate_action
from omega_mail_github_loop_t.command_parser import CommandParseError, parse_command
from omega_mail_github_loop_t.convergence import evaluate_convergence, progress_score
from omega_mail_github_loop_t.engine import dry_run_email
from omega_mail_github_loop_t.evidence import EvidenceLedger
from omega_mail_github_loop_t.models import GitAction, IterationMetrics, LoopCase, LoopDecision, LoopPolicy, MailCommand
from omega_mail_github_loop_t.workflow import create_case, plan

EMAIL = """Bonjour,

OMEGA-GITHUB:
repo: Tristan-TM-Poly/TFUGA-AI7-TRISTAN2
action: improve
target: omega_inbox_outcome_t/intent.py
objective: Réduire les faux positifs du classificateur
required:
  - ajouter des frontières lexicales
  - ajouter cinq tests de régression
authority:
  create_issue: yes
  create_branch: yes
  commit: yes
  open_draft_pr: yes
  merge: no
base_branch: main

Merci.
"""


def test_parse_command():
    command = parse_command(EMAIL, message_id="m1", thread_id="t1", sender="oak@example.test")
    assert command.repository == "Tristan-TM-Poly/TFUGA-AI7-TRISTAN2"
    assert command.target.endswith("intent.py")
    assert len(command.required) == 2
    assert command.authority["merge"] is False
    assert len(command.content_hash()) == 64


def test_parse_rejects_missing_block():
    with pytest.raises(CommandParseError, match="missing_omega"):
        parse_command("hello")


def test_parse_rejects_unsafe_target():
    with pytest.raises(CommandParseError, match="unsafe_target"):
        parse_command(EMAIL.replace("omega_inbox_outcome_t/intent.py", "../secret"))


def test_email_cannot_authorize_merge():
    command = parse_command(EMAIL.replace("merge: no", "merge: yes"))
    result = evaluate_action(command, LoopPolicy(), GitAction.MERGE)
    assert result.allowed is False
    assert any("forbidden" in item or "merge_disabled" in item for item in result.reasons)


def test_default_branch_commit_is_blocked():
    result = evaluate_action(parse_command(EMAIL), LoopPolicy(), GitAction.CREATE_COMMIT)
    assert result.allowed is False
    assert "default_branch_write_forbidden" in result.reasons


def test_branch_and_draft_pr_are_allowed():
    command = parse_command(EMAIL)
    assert evaluate_action(command, LoopPolicy(), GitAction.CREATE_BRANCH).allowed
    assert evaluate_action(command, LoopPolicy(), GitAction.OPEN_DRAFT_PR).allowed


def test_duplicate_command_is_blocked():
    command = parse_command(EMAIL)
    first = evaluate_mail(command, seen_fingerprints=set())
    second = evaluate_mail(command, seen_fingerprints={first.fingerprint})
    assert first.allowed and not second.allowed


def test_auto_ack_is_not_development_work():
    command = parse_command(EMAIL.replace("action: improve", "action: auto_reply"))
    assert not evaluate_mail(command, seen_fingerprints=set()).allowed


def test_workflow_objects_are_deterministic():
    command = parse_command(EMAIL)
    case1 = create_case(command)
    case2 = create_case(command)
    assert case1.case_id == case2.case_id
    objects = plan(case1)
    assert objects.branch_name.startswith("mail-loop/")
    assert "No automatic merge" in objects.draft_pr_body


def test_dry_run_builds_issue_branch_pr_reply():
    result = dry_run_email(EMAIL)
    assert result.anti_loop.allowed
    assert result.objects.issue_title.startswith("[MGC-")
    assert result.objects.branch_name.startswith("mail-loop/")
    assert result.authority["MERGE"].allowed is False
    assert result.case.artifact_hashes


def test_positive_progress_continues():
    metrics = IterationMetrics(tests_added=5, defects_removed=1, cost_units=2)
    assert progress_score(metrics) > 0
    result = evaluate_convergence(LoopCase("x", MailCommand("o/r", "a", "t", "o")), metrics, LoopPolicy())
    assert result.decision is LoopDecision.CONTINUE


def test_acceptance_stops():
    result = evaluate_convergence(LoopCase("x", MailCommand("o/r", "a", "t", "o")), IterationMetrics(), LoopPolicy(), acceptance_satisfied=True)
    assert result.decision is LoopDecision.STOP_ACCEPTED


def test_repeated_no_gain_stops():
    case = LoopCase("x", MailCommand("o/r", "a", "t", "o"), unchanged_reply_count=1)
    assert evaluate_convergence(case, IterationMetrics(cost_units=1), LoopPolicy()).decision is LoopDecision.STOP_NO_GAIN


def test_repeated_failure_stops():
    case = LoopCase("x", MailCommand("o/r", "a", "t", "o"), repeated_failure_count=2)
    assert evaluate_convergence(case, IterationMetrics(tests_added=1), LoopPolicy()).decision is LoopDecision.STOP_REPEATED_FAILURE


def test_budget_stops():
    result = evaluate_convergence(LoopCase("x", MailCommand("o/r", "a", "t", "o")), IterationMetrics(cost_units=10), LoopPolicy(adaptive_cost_budget=5))
    assert result.decision is LoopDecision.STOP_BUDGET


def test_evidence_chain(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    a = ledger.append("MGC-1", "mail_received", {"hash": "a"})
    b = ledger.append("MGC-1", "issue_planned", {"number": 1})
    assert b.previous_hash == a.event_hash
    assert ledger.verify()[0]


def test_evidence_detects_tamper(tmp_path: Path):
    ledger = EvidenceLedger(tmp_path / "evidence.jsonl")
    ledger.append("MGC-1", "mail_received", {"hash": "a"})
    ledger.path.write_text(ledger.path.read_text(encoding="utf-8").replace("mail_received", "mail_changed"), encoding="utf-8")
    assert ledger.verify()[0] is False


def test_atlas_generation_and_audit(tmp_path: Path):
    manifest = generate(tmp_path)
    result = audit(tmp_path)
    assert manifest["shards"] == EXPECTED_SHARDS == 768
    assert manifest["cells"] == EXPECTED_CELLS == 147456
    assert result["passed"] is True


def test_atlas_detects_missing(tmp_path: Path):
    generate(tmp_path)
    next(tmp_path.glob("plan/*/*.cells")).unlink()
    result = audit(tmp_path)
    assert not result["passed"]
    assert result["missing"] == 1
