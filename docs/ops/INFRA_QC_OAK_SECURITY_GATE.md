# INFRA-QC OAK Security Gate

Status: B — safety/security gate
Date: 2026-07-06

## 0. Purpose

This gate prevents the InfrastructureGraph Quebec system from publishing sensitive, exploitable or unsafe information.

## 1. Publication tiers

| Tier | Meaning | Public by default? |
|---|---|---|
| public | already public, non-sensitive, aggregated | yes |
| review | may be public after review and redaction | no |
| restricted | operational detail for authorized parties | no |
| critical | sensitive security or continuity information | never public by default |

## 2. Automatic blockers

Block public output when the content contains:

- exact sensitive locations not already public ;
- access paths ;
- security configurations ;
- detailed dependency chains that could be misused ;
- emergency plans not already public ;
- personal data ;
- unreviewed information about vulnerable communities ;
- real-time operational status of critical assets ;
- instructions that would make harm easier.

## 3. Safe public output

Prefer:

```text
aggregated risk bands
general maintenance priorities
publicly sourced condition summaries
high-level resilience scenarios
non-sensitive asset categories
redacted dependency maps
OAK status and limitations
```

## 4. Context requirements

```yaml
source_is_authorized: required
human_review_for_real_assets: required
redaction_applied: required_if_sensitive
community_context_review: required_if_community_impact
security_review: required_if_critical
```

## 5. Final rule

```text
If an output could help improve infrastructure, keep it.
If it could help target infrastructure, restrict or remove it.
```
