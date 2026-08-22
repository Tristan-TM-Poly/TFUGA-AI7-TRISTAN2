# Ω-META-GTNT-T∞²

Executable prototype for the Gödel–Turing–von Neumann–Tristan metatheory.

## What is implemented

- six-way frontier diagnosis: logical / computational / architectural / representational / informational / epistemic;
- explicit failure taxonomy;
- representation ranking with transparent weights;
- operational order/commutator advantage from measured costs;
- strategy-path scoring by verified gain per total cost;
- `M⁻` / `NoGoRule` pruning;
- epistemic ledger gates `T0..T8`;
- recursion/cycle/descent firewall.

## Run

```bash
python -m omega_meta_gtnt_t demo
python -m omega_meta_gtnt_t diagnose '{"representation_sensitive":true,"poor_conditioning":true}'
pytest -q tests/test_omega_meta_gtnt_t.py
```

## Design rule

The implementation is intentionally conservative. Operational symptoms are not promoted into classical logical results:

- `proof_absent` does not imply independence;
- `termination_unknown` does not imply undecidability;
- numerical agreement does not imply kernel verification;
- hardware/runtime limits do not imply non-computability.

See `docs/canon/OMEGA-META-GTNT-T-CANON-v0.1.md` for the formal architecture and OAK boundaries.
