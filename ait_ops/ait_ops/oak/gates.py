from __future__ import annotations
from ait_ops.core.models import OpsPolicy, GitHubOpsPlan, CloudServerPlan, GateReport


def gate_github(plan: GitHubOpsPlan, policy: OpsPolicy, tests_green=False, ci_green=False, human_approved=False) -> GateReport:
    checks = {
        'branch_not_main': plan.branch not in {'main', 'master'},
        'draft_pr_default': plan.draft_pr is True,
        'push_disabled_or_allowed': (not plan.push_enabled) or policy.allow_git_push,
        'merge_disabled_or_allowed': (not plan.merge_enabled) or policy.allow_merge,
        'tests_green': tests_green,
        'ci_green': ci_green,
        'human_or_policy': human_approved or (policy.allow_merge and not policy.human_approval_required),
    }
    risks = []
    if not tests_green: risks.append('tests not confirmed green')
    if not ci_green: risks.append('CI not confirmed green')
    score = sum(checks.values()) / len(checks) - 0.04 * len(risks)
    score = max(0.0, min(1.0, score))
    merge_allowed = score >= policy.oak_threshold and plan.merge_enabled and policy.allow_merge and tests_green and ci_green and checks['human_or_policy']
    return GateReport('merge_allowed' if merge_allowed else 'github_plan_ready_pr_draft', score, checks, risks, ['default_branch_direct_write', 'history_rewrite', 'merge_without_gate'], 'Open draft PR; merge only after tests, CI and approval.')


def gate_cloud(plan: CloudServerPlan, policy: OpsPolicy, human_approved=False, rollback_confirmed=False) -> GateReport:
    checks = {
        'deploy_disabled_or_allowed': (not plan.deploy_enabled) or policy.allow_provider_api,
        'remote_access_disabled_or_approved': policy.allow_remote_access is False or human_approved,
        'sensitive_material_disabled': policy.allow_sensitive_material is False,
        'dry_run_default': policy.dry_run_default is True,
        'rollback_present': bool(plan.rollback),
        'rollback_confirmed': rollback_confirmed or not plan.deploy_enabled,
        'security_checks_present': bool(plan.security_checks),
        'cost_checks_present': bool(plan.cost_checks),
        'human_for_prod': plan.environment != 'production' or human_approved,
    }
    risks = []
    if plan.deploy_enabled and not policy.allow_provider_api: risks.append('deploy enabled but provider API disabled by policy')
    if plan.environment == 'production' and not human_approved: risks.append('production requires human approval')
    score = sum(checks.values()) / len(checks) - 0.04 * len(risks)
    score = max(0.0, min(1.0, score))
    deploy_allowed = score >= policy.oak_threshold and plan.deploy_enabled and policy.allow_provider_api and (plan.environment != 'production' or human_approved)
    return GateReport('deploy_allowed' if deploy_allowed else 'cloud_plan_ready_dry_run', score, checks, risks, ['destructive_cloud_action', 'prod_deploy_without_approval'], 'Run dry-run first; deploy only with approval and rollback.')
