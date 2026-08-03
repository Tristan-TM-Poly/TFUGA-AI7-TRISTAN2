from ait_ops.github.manager import build_github_plan
from ait_ops.clouds.manager import build_cloud_server_plan
from ait_ops.oak.gates import gate_github, gate_cloud
from ait_ops.core.models import OpsPolicy


def run():
    gh = build_github_plan('prepare PR and staging dry run')
    cloud = build_cloud_server_plan('staging docker dry run')
    policy = OpsPolicy()
    assert gh.branch.startswith('codex/')
    assert gh.draft_pr is True
    assert gh.push_enabled is False
    assert gh.merge_enabled is False
    assert cloud.deploy_enabled is False
    assert gate_github(gh, policy).status == 'github_plan_ready_pr_draft'
    assert gate_cloud(cloud, policy).status == 'cloud_plan_ready_dry_run'
    merge_policy = OpsPolicy(allow_merge=True, human_approval_required=False)
    gh.merge_enabled = True
    assert gate_github(gh, merge_policy, tests_green=True, ci_green=True).status == 'merge_allowed'
    print('ALL TESTS PASSED')


if __name__ == '__main__':
    run()
