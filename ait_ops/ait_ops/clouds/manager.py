from __future__ import annotations
from ait_ops.core.models import CloudServerPlan


def infer_provider(intent: str) -> str:
    t = intent.lower()
    if 'aws' in t: return 'aws'
    if 'gcp' in t or 'google cloud' in t: return 'gcp'
    if 'azure' in t: return 'azure'
    if 'docker' in t: return 'docker'
    if 'kubernetes' in t or 'k8s' in t: return 'kubernetes'
    return 'generic_cloud'


def build_cloud_server_plan(intent: str, environment: str = 'staging') -> CloudServerPlan:
    provider = infer_provider(intent)
    actions = ['inventory target resources', 'generate dry-run deployment plan', 'run tests before deploy', 'prepare rollback before deploy', 'record audit log']
    runbook = ['confirm environment and owner', 'confirm cost budget and quotas', 'run dry-run plan', 'review change set', 'run tests and health checks', 'deploy only after approval', 'monitor and rollback if health fails']
    dry_run_commands = ['terraform plan', 'ansible-playbook --check site.yml', 'docker compose config', 'kubectl diff -f k8s/']
    blocked = ['destructive infrastructure changes', 'namespace wipe', 'filesystem wipe', 'firewall disabled', 'public admin exposure']
    rollback = ['revert deployment artifact', 'restore previous image tag', 'rollback Kubernetes deployment', 'restore verified backup when data changed']
    security = ['least privilege IAM', 'no sensitive material in repo', 'remote keys outside generated files', 'TLS for public services', 'firewall reviewed']
    cost = ['budget cap reviewed', 'instance sizes reviewed', 'autoscaling limits reviewed', 'orphan resource cleanup plan']
    return CloudServerPlan(environment, provider, f'{provider}:{environment}', actions, runbook, dry_run_commands, blocked, rollback, security, cost, False)
