#!/usr/bin/env python3
"""Ω-HOSTING-T OAK scoring prototype.

This small, dependency-free tool scores whether a component should be hosted on
Hostinger Web, Hostinger VPS, a managed data platform, or a dedicated compute
platform.

It is intentionally conservative. It does not deploy anything; it produces a
risk-oriented decision report that can be attached to a PR or issue.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Literal

AssetClass = Literal[
    "public_open",
    "public_marketing",
    "confidential_ip",
    "private_personal",
    "regulated_sensitive",
    "secrets",
]

ComponentType = Literal[
    "static_site",
    "wordpress_blog",
    "landing_page",
    "n8n",
    "webhook_api",
    "dashboard",
    "database",
    "gpu_compute",
    "ait_agent",
]

HostChoice = Literal[
    "hostinger_web",
    "hostinger_cloud",
    "hostinger_vps",
    "github",
    "vercel_or_cloudflare",
    "supabase_or_managed_postgres",
    "dedicated_gpu_or_local_compute",
    "block_until_review",
]


@dataclass(frozen=True)
class HostingInput:
    component_type: ComponentType
    asset_class: AssetClass
    public_exposure: bool = False
    stores_state: bool = False
    needs_gpu: bool = False
    uses_external_actions: bool = False
    sends_email_or_messages: bool = False
    handles_payments_or_legal: bool = False
    contains_private_data: bool = False
    contains_secrets_in_repo: bool = False
    reveals_unreviewed_ip: bool = False
    rollback_defined: bool = False
    backups_defined: bool = False
    human_approval_gate: bool = False


@dataclass
class HostingDecision:
    score: int
    max_score: int
    decision: HostChoice
    allowed: bool
    risk_level: Literal["low", "medium", "high", "critical"]
    reasons: list[str] = field(default_factory=list)
    required_actions: list[str] = field(default_factory=list)


def evaluate(plan: HostingInput) -> HostingDecision:
    score = 16
    reasons: list[str] = []
    actions: list[str] = []

    def penalize(points: int, reason: str, action: str | None = None) -> None:
        nonlocal score
        score -= points
        reasons.append(reason)
        if action:
            actions.append(action)

    hard_block = False

    if plan.contains_secrets_in_repo:
        hard_block = True
        penalize(8, "Repository appears to contain secret material.", "Remove secrets, rotate exposed values, and use a secret manager.")

    if plan.reveals_unreviewed_ip:
        hard_block = True
        penalize(6, "Plan may reveal confidential or patentable IP before review.", "Run IP/OAK review and publish only filtered public material.")

    if plan.asset_class in {"confidential_ip", "private_personal", "regulated_sensitive", "secrets"} and plan.public_exposure:
        hard_block = True
        penalize(8, f"Asset class {plan.asset_class!r} cannot be publicly exposed.", "Reclassify, redact, privatize, or block publication.")

    if plan.contains_private_data:
        penalize(4, "Component handles private data.", "Minimize data, encrypt, restrict access, and document retention.")

    if plan.needs_gpu:
        penalize(3, "Component needs GPU/heavy compute.", "Use dedicated GPU/local compute instead of shared hosting or small VPS.")

    if plan.stores_state and not plan.backups_defined:
        penalize(3, "Stateful component without backup plan.", "Define snapshots, restore test, and backup retention.")

    if not plan.rollback_defined:
        penalize(2, "Rollback is not defined.", "Add revert/redeploy/restore recipe before deployment.")

    if plan.uses_external_actions and not plan.human_approval_gate:
        penalize(3, "External actions lack human approval gate.", "Add approval queue for sensitive external actions.")

    if plan.sends_email_or_messages and not plan.human_approval_gate:
        hard_block = True
        penalize(5, "Email/message sending requires explicit approval gate.", "Use draft-only mode until approved.")

    if plan.handles_payments_or_legal and not plan.human_approval_gate:
        hard_block = True
        penalize(6, "Payment/legal actions require human approval.", "Block automation and require explicit approval.")

    if score >= 13:
        risk = "low"
    elif score >= 10:
        risk = "medium"
    elif score >= 6:
        risk = "high"
    else:
        risk = "critical"

    decision: HostChoice
    if hard_block or score < 8:
        decision = "block_until_review"
        allowed = False
    elif plan.component_type in {"static_site", "landing_page", "wordpress_blog"}:
        decision = "hostinger_web" if plan.component_type != "static_site" else "vercel_or_cloudflare"
        allowed = True
    elif plan.component_type in {"n8n", "webhook_api", "ait_agent"} and not plan.needs_gpu:
        decision = "hostinger_vps"
        allowed = True
    elif plan.component_type == "database":
        decision = "supabase_or_managed_postgres"
        allowed = True
    elif plan.component_type == "gpu_compute" or plan.needs_gpu:
        decision = "dedicated_gpu_or_local_compute"
        allowed = True
    else:
        decision = "hostinger_cloud"
        allowed = True

    # Deduplicate required actions while preserving order.
    seen = set()
    unique_actions = []
    for action in actions:
        if action not in seen:
            unique_actions.append(action)
            seen.add(action)

    return HostingDecision(
        score=max(score, 0),
        max_score=16,
        decision=decision,
        allowed=allowed,
        risk_level=risk,
        reasons=reasons or ["No blocking risk detected by the prototype scorer."],
        required_actions=unique_actions,
    )


def parse_bool(value: str) -> bool:
    lowered = value.lower().strip()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score an Ω-HOSTING-T deployment plan.")
    parser.add_argument("--component-type", required=True, choices=list(ComponentType.__args__))
    parser.add_argument("--asset-class", required=True, choices=list(AssetClass.__args__))
    for field_name in [
        "public_exposure",
        "stores_state",
        "needs_gpu",
        "uses_external_actions",
        "sends_email_or_messages",
        "handles_payments_or_legal",
        "contains_private_data",
        "contains_secrets_in_repo",
        "reveals_unreviewed_ip",
        "rollback_defined",
        "backups_defined",
        "human_approval_gate",
    ]:
        parser.add_argument(f"--{field_name.replace('_', '-')}", type=parse_bool, default=False)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = HostingInput(
        component_type=args.component_type,
        asset_class=args.asset_class,
        public_exposure=args.public_exposure,
        stores_state=args.stores_state,
        needs_gpu=args.needs_gpu,
        uses_external_actions=args.uses_external_actions,
        sends_email_or_messages=args.sends_email_or_messages,
        handles_payments_or_legal=args.handles_payments_or_legal,
        contains_private_data=args.contains_private_data,
        contains_secrets_in_repo=args.contains_secrets_in_repo,
        reveals_unreviewed_ip=args.reveals_unreviewed_ip,
        rollback_defined=args.rollback_defined,
        backups_defined=args.backups_defined,
        human_approval_gate=args.human_approval_gate,
    )
    decision = evaluate(plan)
    print(json.dumps({"input": asdict(plan), "decision": asdict(decision)}, indent=2, ensure_ascii=False))
    return 0 if decision.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
