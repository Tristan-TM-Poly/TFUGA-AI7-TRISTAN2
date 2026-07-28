# ARK-SP-CUBE-GAIA — Route to v0.9

Status: C — next-gate roadmap only.

## Objective

Turn the v0.8 claim-route scaffold into a minimal executable review workflow without claiming technical, legal, public-sector or financial validation.

## v0.9 target artifacts

```text
data/claim_ledgers/ark_sp_cube_gaia_claim_ledger_v0_9.csv
failure_synth/ark_sp_cube_gaia_failure_synth_v0_9.json
docs/public_site/ARK_SP_CUBE_GAIA_PROOF_LEDGER_SEED.md
docs/oakshield_core/ARK_SP_CUBE_GAIA_CLAIM_STYLE.md
reports/examples/ark_sp_cube_gaia_demo/README.md
reports/examples/ark_sp_cube_gaia_demo/ark_sp_cube_gaia_demo_bundle.json
```

## Route map

| Source | v0.9 action | Output |
|---|---|---|
| Claim ledger v0.8 | Normalize statuses and next gates | Stable CSV |
| FailureSynth v0.8 | Convert failures to local review drafts | OAK issue draft seed |
| SP-CUBE claims | Add thermal/spectral non-claim templates | OAKShield style guide |
| GAIA claims | Add MRV/value non-claim templates | OAKShield style guide |
| ARK claims | Add low-voltage experimental safety language | OAKShield style guide |
| Infra/Gov modules | Produce demo bundle shape | Review-safe demo pack |
| 8e Feu | Produce proof-ledger seed | Public-safe copy |

## Minimum executable gate

A v0.9 PR should be considered successful if it adds:

1. one stable claim ledger;
2. one stable failure register;
3. one proof-ledger seed;
4. one OAKShield claim-style page;
5. one demo bundle shape;
6. no remote mutation by default;
7. no certification, revenue, legal or operational overclaim.

## Suggested command names for later code PR

```bash
python -m ark_sp_cube_gaia claim-ledger --out data/claim_ledgers/ark_sp_cube_gaia_claim_ledger.csv
python -m ark_sp_cube_gaia failures --out failure_synth/ark_sp_cube_gaia_failure_synth.json
python -m ark_sp_cube_gaia proof-ledger --out docs/public_site/ARK_SP_CUBE_GAIA_PROOF_LEDGER_SEED.md
python -m ark_sp_cube_gaia demo --out reports/examples/ark_sp_cube_gaia_demo
```

## R5 close

This route is intentionally small: it makes the circulation visible before adding automation. No physical or financial claim becomes stronger until evidence becomes stronger.
