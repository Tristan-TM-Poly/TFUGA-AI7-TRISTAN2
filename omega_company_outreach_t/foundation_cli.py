from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping

from .foundation.canonical import CanonicalizationError, canonical_hash
from .foundation.contacts import RoleCategory
from .foundation.consent import ConsentBasis, ConsentScope
from .foundation.event_store import CanonicalEventStore
from .foundation.events import build_outreach_projection
from .foundation.identity import CompanyIdentity, DomainClaim, IdentityState
from .foundation.migration import MigrationIds
from .foundation.migration_runtime import migrate_case_file
from .foundation.opportunities import OpportunityType, StrategicSignals
from .foundation.organizations import OrganizationType
from .foundation.scenario_runtime import audit_atlas_directory, write_atlas
from .foundation.scenario_atlas import theoretical_cardinality
from .foundation.schemas import audit_schema_catalog, write_schema_catalog


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in value]
    return value


def _print(value: Any) -> None:
    print(json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, indent=2))


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CanonicalizationError(f"{path} must contain a JSON object")
    return payload


def _load_signals(path: Path) -> StrategicSignals:
    payload = _load_object(path)
    expected = set(StrategicSignals.__dataclass_fields__)
    missing = expected - set(payload)
    unknown = set(payload) - expected
    if missing:
        raise CanonicalizationError(f"strategic signals missing fields: {sorted(missing)}")
    if unknown:
        raise CanonicalizationError(f"strategic signals contain unknown fields: {sorted(unknown)}")
    return StrategicSignals(**{key: float(value) for key, value in payload.items()})


def _migration_ids(prefix: int) -> MigrationIds:
    if prefix < 1 or prefix > 4999:
        raise CanonicalizationError("migration prefix must be between 1 and 4999")
    return MigrationIds(
        organization_id=f"ORG-2026-{prefix:04d}",
        contact_id=f"CNT-2026-{prefix:04d}",
        consent_id=f"CONSENT-2026-{prefix:04d}",
        opportunity_id=f"OPP-2026-{prefix:04d}",
        evidence_id=f"EVID-2026-{prefix:04d}",
        contact_evidence_id=f"EVID-2026-{prefix + 5000:04d}",
        event_ids=tuple(f"EVT-2026-{prefix * 10 + index:04d}" for index in range(1, 6)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-outreach-foundation",
        description="Ω Company Outreach R1.0 identity, organization, contact and event foundation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    identity = sub.add_parser("identity-example", help="Build and validate a company identity")
    identity.add_argument("--company-id", default="tristan_software_labs")
    identity.add_argument("--display-name", default="Tristan Software Labs")
    identity.add_argument(
        "--state", choices=[state.value for state in IdentityState], default="internal_role"
    )
    identity.add_argument("--purpose", action="append", default=[])
    identity.add_argument("--domain")
    identity.add_argument("--verified-domain", action="store_true")
    identity.add_argument("--domain-evidence-hash")

    event_audit = sub.add_parser("event-audit", help="Audit an append-only event store")
    event_audit.add_argument("event_store", type=Path)

    project = sub.add_parser("event-project", help="Build an outreach projection")
    project.add_argument("event_store", type=Path)
    project.add_argument("--out", type=Path)

    migrate = sub.add_parser("migrate-case", help="Migrate one R0.2 outreach case")
    migrate.add_argument("source", type=Path)
    migrate.add_argument("destination", type=Path)
    migrate.add_argument("--id-prefix", type=int, required=True)
    migrate.add_argument(
        "--organization-type",
        choices=[item.value for item in OrganizationType],
        required=True,
    )
    migrate.add_argument(
        "--opportunity-type",
        choices=[item.value for item in OpportunityType],
        required=True,
    )
    migrate.add_argument(
        "--role-category", choices=[item.value for item in RoleCategory], required=True
    )
    migrate.add_argument(
        "--consent-basis", choices=[item.value for item in ConsentBasis], required=True
    )
    migrate.add_argument(
        "--consent-scope", choices=[item.value for item in ConsentScope], required=True
    )
    migrate.add_argument("--signals", type=Path, required=True)
    migrate.add_argument("--asset", required=True)
    migrate.add_argument("--organization-domain")

    atlas_generate = sub.add_parser("atlas-generate", help="Generate deterministic OAK scenarios")
    atlas_generate.add_argument("directory", type=Path)
    atlas_generate.add_argument("--count", type=int, default=8192)
    atlas_generate.add_argument("--seed", type=int, default=20260802)
    atlas_generate.add_argument("--shard-size", type=int, default=512)

    atlas_audit = sub.add_parser("atlas-audit", help="Audit generated OAK scenarios")
    atlas_audit.add_argument("directory", type=Path)

    sub.add_parser("atlas-cardinality", help="Print theoretical scenario cardinality")

    schemas_generate = sub.add_parser("schemas-generate", help="Generate JSON Schema catalog")
    schemas_generate.add_argument("directory", type=Path)

    schemas_audit = sub.add_parser("schemas-audit", help="Audit JSON Schema catalog")
    schemas_audit.add_argument("directory", type=Path)

    hash_command = sub.add_parser("canonical-hash", help="Hash a JSON object canonically")
    hash_command.add_argument("path", type=Path)
    return parser


def _identity_example(args: argparse.Namespace) -> dict[str, Any]:
    domains: tuple[DomainClaim, ...] = ()
    if args.domain:
        if args.verified_domain:
            domains = (
                DomainClaim(
                    domain=args.domain,
                    verified=True,
                    verification_method="dns_txt",
                    evidence_hash=args.domain_evidence_hash,
                    verified_at=datetime.now(timezone.utc),
                ),
            )
        else:
            domains = (DomainClaim(domain=args.domain),)
    identity = CompanyIdentity(
        company_id=args.company_id,
        display_name=args.display_name,
        state=IdentityState(args.state),
        purpose=tuple(args.purpose or ["software pilots", "integrations"]),
        domains=domains,
    )
    return {
        "valid": True,
        "identity": identity,
        "identity_hash": identity.identity_hash,
        "disclosure": identity.disclosure_line(),
        "can_claim_corporate_sender": identity.can_claim_corporate_sender(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "identity-example":
            _print(_identity_example(args))
            return 0
        if args.command == "event-audit":
            audit = CanonicalEventStore(args.event_store).audit()
            _print(audit)
            return 0 if audit.valid else 2
        if args.command == "event-project":
            store = CanonicalEventStore(args.event_store)
            audit = store.audit()
            if not audit.valid:
                _print(audit)
                return 2
            projection = build_outreach_projection(store.read_all())
            payload = _jsonable(
                {
                    "projection": projection,
                    "projection_hash": projection.projection_hash,
                    "event_store_audit": audit,
                }
            )
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(
                    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
                    encoding="utf-8",
                )
            _print(payload)
            return 0
        if args.command == "migrate-case":
            output = migrate_case_file(
                args.source,
                args.destination,
                ids=_migration_ids(args.id_prefix),
                organization_type=OrganizationType(args.organization_type),
                opportunity_type=OpportunityType(args.opportunity_type),
                role_category=RoleCategory(args.role_category),
                consent_basis=ConsentBasis(args.consent_basis),
                consent_scope=ConsentScope(args.consent_scope),
                strategic_signals=_load_signals(args.signals),
                proposed_asset_id=args.asset,
                organization_domain=args.organization_domain,
            )
            _print(
                {
                    "valid": True,
                    "destination": str(args.destination),
                    "migration_hash": output["migration_hash"],
                    "source_case_hash": output["source_case_hash"],
                }
            )
            return 0
        if args.command == "atlas-generate":
            manifest = write_atlas(
                args.directory,
                count=args.count,
                seed=args.seed,
                shard_size=args.shard_size,
            )
            _print(manifest)
            return 0
        if args.command == "atlas-audit":
            result = audit_atlas_directory(args.directory)
            _print(result)
            return 0 if result["valid"] else 2
        if args.command == "atlas-cardinality":
            _print({"theoretical_cardinality": theoretical_cardinality()})
            return 0
        if args.command == "schemas-generate":
            catalog = write_schema_catalog(args.directory)
            _print(catalog)
            return 0
        if args.command == "schemas-audit":
            errors = audit_schema_catalog(args.directory)
            _print({"valid": not errors, "errors": errors})
            return 0 if not errors else 2
        if args.command == "canonical-hash":
            payload = json.loads(args.path.read_text(encoding="utf-8"))
            _print({"canonical_hash": canonical_hash(payload)})
            return 0
    except (CanonicalizationError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        _print({"valid": False, "error": str(exc), "command": args.command})
        return 2
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
