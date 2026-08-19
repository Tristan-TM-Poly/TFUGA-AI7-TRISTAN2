# ARK-SP-CUBE-GAIA Diversification Max v0.14

Status: `C_plus_diversification_scaffold`

This document starts the post-merge diversification layer after PR #232. It does not add new scientific validation, revenue claims, patent claims, or certification. It splits the merged v0.8-v0.13 spine into parallel tracks that can evolve as smaller reviewable PRs.

## Core rule

```text
One spine, many organs, no claim without a test.
```

## Diversification tracks

| Track | Name | Purpose | First output | OAK boundary |
|---|---|---|---|---|
| D1 | SP-CUBE Passive Lab | Move from protocol to measured candidate | delta-T data schema and logger plan | Not cooling certification |
| D2 | Ark-M1 Bench | Build a low-power safe bench path | BOM, wiring safety, sensor map | Not energy product validation |
| D3 | Methane MRV | Make the fastest climate-impact branch concrete | anti-double-count event schema v0.15 | Not certified offset issuance |
| D4 | OAK Tooling | Turn OAK-Lint into runnable checks | CLI lint report and CI gate proposal | Not a replacement for human review |
| D5 | Public-Safe Dashboard | Improve public readability without hype | static HTML portfolio page | Not investor or revenue proof |
| D6 | Thesis/Patent Route | Route claims into thesis/patent-style records | claim tree and risk map | Not legal patent validity |
| D7 | Infra/Gov Integration | Connect GAIA events to Infra-QC/Gov-QC style graphs | source/risk/severity graph draft | Not public-sector decision |
| D8 | Sensor Logger | Prepare physical logging stack | ESP32/Python serial logger scaffold | Not calibrated instrument certification |
| D9 | Citations/Sources | Replace TODO source slots with verified references | source registry follow-up | Not complete bibliography yet |
| D10 | FailureSynth Expansion | Convert failure modes into local issues | failure-to-issue routing table | No remote issues unless explicit confirmation |

## OAK diversification invariants

```yaml
no_new_certification_claim: true
no_revenue_claim: true
no_energy_from_vacuum_claim: true
no_public_decision_authority: true
no_remote_issue_creation_without_explicit_confirmation: true
human_review_required: true
```

## Recommended split PRs after this scaffold

1. `v0.15-spcube-logger-data-schema`
2. `v0.15-ark-m1-bom-safety-map`
3. `v0.15-methane-mrv-event-schema`
4. `v0.15-oak-lint-cli-ci-gate`
5. `v0.15-public-safe-portfolio-dashboard`
6. `v0.15-thesis-patent-claim-tree`
7. `v0.15-infra-gov-graph-routing`

## Freeze note

This v0.14 PR should remain a map and routing layer. The next work should be split into smaller PRs, each with one proof path and one failure path.
