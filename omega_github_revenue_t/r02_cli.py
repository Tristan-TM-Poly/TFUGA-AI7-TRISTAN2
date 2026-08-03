from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .atlas import default_system_atlas
from .authorization import AuditAuthorization, Operation
from .campaign import CampaignConfig, run_campaign, synthetic_artifacts
from .conversion import FunnelSnapshot, analyze_funnel, recommend_funnel_action
from .models import SponsorTier
from .oakgate import run_oakgate
from .profile import ProjectCard, SponsorProfile, write_profile_bundle
from .reconciliation import ProviderEvent, reconcile_events
from .store import CampaignStore


def _dump(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def command_audit(args: argparse.Namespace) -> int:
    root = Path(args.repository).resolve()
    authorization = AuditAuthorization(
        authorization_id=args.authorization_id,
        repository_id=str(root),
        granted_by=args.granted_by,
        granted_at=args.granted_at,
        expires_at=args.expires_at,
        operations=tuple(Operation),
        explicitly_authorized=args.i_am_authorized,
        purpose=args.purpose,
    )
    report, receipt = run_oakgate(root, authorization, args.output)
    _dump(
        {
            "report": report.to_dict(),
            "receipt": receipt.to_dict(),
            "output": args.output,
        }
    )
    return 0


def command_campaign(args: argparse.Namespace) -> int:
    store = CampaignStore(args.database)
    config = CampaignConfig(
        campaign_id=args.campaign_id,
        checkpoint_every=args.checkpoint_every,
        initial_batch_size=args.initial_batch_size,
        minimum_score=args.minimum_score,
        stop_after=args.stop_after,
    )
    receipt = run_campaign(
        synthetic_artifacts(args.count, namespace=args.namespace),
        store,
        config,
    )
    _dump(
        {
            "receipt": receipt.to_dict(),
            "database": args.database,
            "artifact_count": store.count_artifacts(),
        }
    )
    return 0


def command_atlas(_: argparse.Namespace) -> int:
    _dump(default_system_atlas())
    return 0


def command_funnel(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    snapshot = FunnelSnapshot(**payload)
    _dump(
        {
            "analysis": analyze_funnel(snapshot),
            "next_action": recommend_funnel_action(snapshot),
        }
    )
    return 0


def command_reconcile(args: argparse.Namespace) -> int:
    def read(path: str) -> list[ProviderEvent]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("reconciliation files must contain a JSON array")
        return [ProviderEvent(**item) for item in payload]

    _dump(reconcile_events(read(args.internal), read(args.provider)))
    return 0


def command_profile(args: argparse.Namespace) -> int:
    profile = SponsorProfile(
        handle="Tristan-TM-Poly",
        display_name="Tristan Tardif-Morency — OAK Research Software",
        mission=(
            "I build proof-carrying research software that converts ambitious ideas "
            "into bounded claims, reproducible tests, documented limitations, and "
            "useful open-source artifacts."
        ),
        public_commitments=(
            "separate hypotheses, demonstrations, transactions, and validated outcomes",
            "publish tests, limitations, provenance, and negative results where safe",
            "keep banking, tax, credentials, client data, and patent-sensitive material private",
            "use sponsorship to maintain public research software rather than promise private outcomes",
        ),
        non_claims=(
            "sponsorship is not an investment or promise of return",
            "repository volume is not scientific proof or commercial traction",
            "custom services require a separate bounded agreement",
        ),
        projects=(
            ProjectCard(
                "OAKGate Repository Audit",
                (
                    "Authorized static repository audit with privacy-minimized findings "
                    "and evidence receipts."
                ),
                "D — demonstrated locally",
                (
                    "deterministic audit",
                    "authorization gate",
                    "tests and CI",
                    "Merkle evidence manifest",
                ),
                "complete one consented external pilot and measure utility",
                "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
            ),
            ProjectCard(
                "Ω-SANS-PLAFOND-T∞",
                (
                    "Adaptive finite campaigns with streaming, checkpoints, "
                    "deduplication, and rollback planning."
                ),
                "D — demonstrated locally",
                (
                    "frontier tests beyond 10k",
                    "disk-backed planning",
                    "explicit non-claims",
                ),
                "benchmark larger finite campaigns and publish resource curves",
                "https://github.com/Tristan-TM-Poly/TFUGA-AI7-TRISTAN2",
            ),
        ),
        tiers=(
            SponsorTier(
                "Supporter",
                500,
                "USD",
                0,
                ("support public maintenance",),
            ),
            SponsorTier(
                "Research Follower",
                1500,
                "USD",
                5,
                ("collective public progress note",),
            ),
            SponsorTier(
                "Prototype Backer",
                5000,
                "USD",
                15,
                ("selected public experimental release briefing",),
            ),
            SponsorTier(
                "Research Patron",
                15000,
                "USD",
                45,
                ("periodic collective technical briefing",),
            ),
        ),
        contact_note=(
            "Public questions belong in repository discussions; private work requires "
            "explicit scope and consent."
        ),
    )
    _dump(write_profile_bundle(profile, args.output))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-github-revenue-r02")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser(
        "oakgate-audit",
        help="audit one local repository with explicit authorization",
    )
    audit.add_argument("repository")
    audit.add_argument("--output", required=True)
    audit.add_argument("--authorization-id", required=True)
    audit.add_argument("--granted-by", required=True)
    audit.add_argument("--granted-at", required=True)
    audit.add_argument("--expires-at")
    audit.add_argument("--purpose", default="bounded repository quality audit")
    audit.add_argument(
        "--i-am-authorized",
        action="store_true",
        help="required explicit authorization assertion",
    )
    audit.set_defaults(func=command_audit)

    campaign = sub.add_parser(
        "campaign",
        help="run a deterministic synthetic capacity campaign",
    )
    campaign.add_argument("--count", type=int, required=True)
    campaign.add_argument("--database", required=True)
    campaign.add_argument("--campaign-id", default="omega-github-revenue-r02")
    campaign.add_argument("--namespace", default="SYNTH")
    campaign.add_argument("--checkpoint-every", type=int, default=1000)
    campaign.add_argument("--initial-batch-size", type=int, default=256)
    campaign.add_argument("--minimum-score", type=float, default=0.0)
    campaign.add_argument("--stop-after", type=int)
    campaign.set_defaults(func=command_campaign)

    atlas = sub.add_parser("atlas", help="emit the system evidence/revenue atlas")
    atlas.set_defaults(func=command_atlas)

    funnel = sub.add_parser("funnel", help="analyze an observed funnel snapshot")
    funnel.add_argument("input")
    funnel.set_defaults(func=command_funnel)

    reconcile = sub.add_parser(
        "reconcile",
        help="compare minimized internal and provider event exports",
    )
    reconcile.add_argument("internal")
    reconcile.add_argument("provider")
    reconcile.set_defaults(func=command_reconcile)

    profile = sub.add_parser(
        "profile",
        help="compile a reviewable Sponsor/profile bundle",
    )
    profile.add_argument("--output", required=True)
    profile.set_defaults(func=command_profile)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, PermissionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
