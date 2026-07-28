# ARK-SP-CUBE-GAIA v0.13 PR Review Freeze

Status: `C_plus_review_freeze_scaffold`

This document freezes the scope of PR #232 after the v0.13 safety and validation layer.

## Why freeze now

The PR now spans:

- v0.8 claim routes and synergy map;
- v0.9 proof ledger, OAKShield style, local issue drafts;
- v0.10 SP-CUBE, Ark-M1 and methane protocol scaffolds;
- v0.11 protocol checklists, citations registry, mini dashboard;
- v0.12 executable checklist JSON, snapshot bundle, static HTML dashboard;
- v0.13 OAK-Lint rules, validation script, validation report and freeze checklist.

Adding more modules now would make review harder and reduce OAK clarity.

## Reviewer checklist

### OAK boundaries

- [ ] No revenue claim.
- [ ] No certified carbon credit claim.
- [ ] No physical performance certification claim.
- [ ] No patent validity claim.
- [ ] No public-sector decision claim.
- [ ] Human review remains required.

### Artifact shape

- [ ] JSON artifacts parse.
- [ ] Snapshot bundle is clearly labeled as demonstration/scaffold.
- [ ] Dashboard states limits as clearly as opportunities.
- [ ] Citation registry does not pretend verification is complete.
- [ ] Validation script scope is narrow and honest.

### Experiment boundary

- [ ] SP-CUBE protocol is a passive comparison protocol, not a certified performance test.
- [ ] Ark-M1 protocol is low-power and safety-first.
- [ ] Methane registry includes anti-double-counting and uncertainty language.

### Merge-readiness question

The PR is ready for merge only if the reviewer can answer:

```text
What is an idea, what is simulated, what is coded, what is locally checkable, and what is explicitly not certified?
```

## Freeze rule

Allowed after v0.13:

- typo fixes;
- safety wording fixes;
- JSON parse fixes;
- validation script fixes;
- citation metadata fixes;
- reviewer-requested clarifications.

Blocked after v0.13 unless new PR:

- new modules;
- new product claims;
- new valuation claims;
- new dashboards not tied to review;
- new scientific claims without measurement;
- remote issue creation automation.

## Canon

A frozen PR is not a smaller dream. It is a dream that finally becomes reviewable.
