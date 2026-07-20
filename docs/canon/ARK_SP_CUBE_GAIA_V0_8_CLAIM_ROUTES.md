# ARK-SP-CUBE-GAIA v0.8 — Claim Routes Canon

Status: C — integration scaffold, not technical validation.

This canon connects the recent executable repository organs into one review-safe route for ARK-M1, SP-CUBE, GAIA-SAT and OAKShield.

## Core route

```text
Idea -> Thesis Seed -> Patent-like Technical Record -> OAK Claim Ledger -> FailureSynth -> Infra/Gov Graph -> Review Issue -> Public Proof Ledger
```

## Module roles

| Module | Role | OAK boundary |
|---|---|---|
| ARK-M1 | Low-power energy management and thermal bench concept | Not a certified energy device |
| SP-CUBE | Spectrally selective radiative cooling / thermal dissipation concept | Not free energy; not physically certified |
| GAIA-SAT | Climate/MRV scoring and value hypothesis layer | Simulated value is not revenue or credit |
| OAKShield | Claim-style and review boundary guard | Guardrail, not external validation |
| Omega Thesis | Converts idea to structured thesis/code/git seeds | Scaffold is not proof |
| Omega Patent Thesis | Converts records to claim trees, risks and review cards | Patent-like is not patent filing or legal conclusion |
| Omega Infra QC | Represents assets, dependencies, evidence and risks | Demo/audit support, not final decision |
| Omega Gov QC | Converts evidence/risk signals to local issue drafts and severity | Local review only; no institutional authority |
| 8e Feu | Public trust and proof-ledger translation | Public copy must not outrun evidence |

## Integration invariant

Every public or product-facing statement must route through a claim state:

```text
UNKNOWN -> FORMALIZED -> SIMULATED -> PROTOTYPED -> MEASURED -> CERTIFIED
```

No claim may skip directly from FORMALIZED or SIMULATED to CERTIFIED.

## Canon equation

```text
ARK_SP_GAIA_v0_8 = OAKShield(
  ThesisRoute(ARK, SP_CUBE, GAIA),
  PatentRiskMap,
  InfraGraph,
  GovIssueSeverity,
  PublicProofLedger
)
```

## Non-claims

This integration does not claim:

- validated climate credits;
- legal patent protection;
- certified physical performance;
- official public-sector finding;
- automated operational decision;
- guaranteed revenue;
- energy generation from vacuum or free energy.

## Next gates

1. Add claim ledger CSV.
2. Add FailureSynth JSON seed.
3. Add route map from each claim to thesis/patent/gov/infra/public modules.
4. Add OAKShield style checks for overclaims.
5. Add a draft PR or issue generator only after local review format stabilizes.
