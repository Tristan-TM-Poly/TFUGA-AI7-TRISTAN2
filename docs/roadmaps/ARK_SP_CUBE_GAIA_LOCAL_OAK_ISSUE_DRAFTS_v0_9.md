# ARK-SP-CUBE-GAIA Local OAK Issue Drafts v0.9

Status: C_local_issue_drafts_only

These are local review drafts inspired by Gov-QC/OAK issue workflows. They do not create remote issues automatically.

## Draft 1: protect GAIA value wording

```yaml
title: "OAK: keep GAIA-SAT values separated from revenue claims"
severity: P0
source_claims:
  - GAIA-001
failure_modes:
  - gross value confused with revenue
  - MRV scenario treated as certified credit
  - OAK-adjusted value presented as investable return
review_checklist:
  - gross/MRV/OAK values are separated
  - every value includes not revenue / not investment certified
  - no certified credit wording without external standard
next_action: add automated claim-style check when wording helper exists
```

## Draft 2: SP-CUBE physical boundary

```yaml
title: "OAK: keep SP-CUBE as radiative-cooling hypothesis until measured"
severity: P1
source_claims:
  - SP-001
failure_modes:
  - energy from vacuum wording
  - cooling guarantee without delta-T data
  - transparent blackbody wording in same passive band/state
review_checklist:
  - spectral separation stated
  - passive/equilibrium limits stated
  - passive plate test listed as next gate
next_action: add passive plate experiment protocol to v0.10
```

## Draft 3: methane MRV uniqueness

```yaml
title: "OAK: methane plume claims require event identity and post-repair verification"
severity: P1
source_claims:
  - METH-001
failure_modes:
  - double counting
  - attribution uncertainty
  - simulated plume presented as detected plume
review_checklist:
  - event ID required
  - source attribution stated
  - uncertainty stated
  - post-repair verification required before measured reduction claim
next_action: add methane event registry schema
```

## Draft 4: ARK-M1 prototype safety

```yaml
title: "OAK: ARK-M1 remains low-power bench until measured safely"
severity: P1
source_claims:
  - ARK-001
failure_modes:
  - reactor wording
  - unsafe battery or heat-source assumption
  - efficiency claim without logger data
review_checklist:
  - low-power constraint stated
  - thermal logger required
  - no high-voltage or hazardous-material path implied
next_action: add ARK-M1 low-power bench protocol
```

## Draft 5: route map integration drift

```yaml
title: "OAK: keep Thesis/Patent/Gov/Infra/8e Feu routes modular"
severity: P2
source_claims:
  - INFRA-001
  - GOV-001
failure_modes:
  - route map mistaken for execution
  - demo viewer mistaken for operational audit
  - public site wording outpaces proof ledger
review_checklist:
  - route_defined stays separate from measured/prototyped
  - public-safe proof ledger used for outward copy
  - human review required for real use
next_action: add route-to-module matrix v0.10
```

## Boundary

These drafts are local planning artifacts only. They do not open remote issues, create labels, assign reviewers, or trigger external action.
