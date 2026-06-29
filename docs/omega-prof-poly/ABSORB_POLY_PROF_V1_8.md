# Omega Absorb Poly Prof v1.8

Status: OAK ledger upgrade.

## Purpose

v1.8 adds OAK manifest plus, lineage ledger, evidence/risk counts, active M-minus rules and OAK ledger CLI helpers.

```text
claims + methods
-> evidence/risk count
-> OAK manifest plus
-> lineage ledger
-> M-minus decision
-> OAK ledger bundle
```

## New modules

- `oak_packet_manifest_plus.py`
- `oak_lineage_ledger.py`
- `evidence_risk_counter.py`
- `mminus_rules_engine.py`
- `oak_ledger_cli.py`

## CLI commands

```bash
omega-absorb evidence-risk --source combined
omega-absorb oak-manifest-plus --source combined
omega-absorb oak-lineage --source combined
omega-absorb mminus-apply --mminus-context unknown_source
omega-absorb oak-ledger --source combined
```

## Tests

```bash
python examples/omega_absorb_poly_prof_v18_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v18.py
```

## v1.9 next targets

1. report atlas;
2. write reports command;
3. release intelligence;
4. generated changelog plus;
5. package CI plan.
