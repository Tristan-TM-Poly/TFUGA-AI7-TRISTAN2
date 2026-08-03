from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

@dataclass
class OpsPolicy:
    allow_network: bool = False
    allow_shell: bool = False
    allow_sensitive_material: bool = False
    allow_git_push: bool = False
    allow_merge: bool = False
    allow_provider_api: bool = False
    allow_remote_access: bool = False
    allow_prod_deploy: bool = False
    human_approval_required: bool = True
    dry_run_default: bool = True
    oak_threshold: float = 0.85
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GitHubOpsPlan:
    repository: str
    branch: str
    commit_message: str
    pr_title: str
    pr_body: str
    draft_pr: bool = True
    push_enabled: bool = False
    merge_enabled: bool = False
    checks_required: List[str] = field(default_factory=lambda: ['tests', 'ci', 'review'])
    rollback: str = 'close PR or revert commit'
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CloudServerPlan:
    environment: str
    provider: str
    target: str
    actions: List[str]
    runbook: List[str]
    dry_run_commands: List[str]
    blocked_commands: List[str]
    rollback: List[str]
    security_checks: List[str]
    cost_checks: List[str]
    deploy_enabled: bool = False
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GateReport:
    status: str
    score: float
    checks: Dict[str, bool]
    risks: List[str]
    blocked: List[str]
    next_action: str
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class OpsPacket:
    intent: str
    policy: OpsPolicy
    github_plan: GitHubOpsPlan
    cloud_plan: CloudServerPlan
    gates: Dict[str, Any]
    next_actions: List[str]
    def to_dict(self) -> Dict[str, Any]:
        return {'intent': self.intent, 'policy': self.policy.to_dict(), 'github_plan': self.github_plan.to_dict(), 'cloud_plan': self.cloud_plan.to_dict(), 'gates': self.gates, 'next_actions': self.next_actions}
