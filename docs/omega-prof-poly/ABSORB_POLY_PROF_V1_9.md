# Omega Absorb Poly Prof v1.9

Status: report atlas and release intelligence upgrade.

## Purpose

v1.9 makes the package self-documenting and ready for v2.0 by adding a report atlas, report writer, release intelligence, changelog plus and CI plan.

```text
status + health + changelog + graph + OAK ledger
-> report atlas
-> report writer
-> release intelligence
-> CI plan
```

## New modules

- `report_atlas.py`
- `report_writer.py`
- `release_intelligence.py`
- `generated_changelog_plus.py`
- `package_ci_plan.py`

## CLI commands

```bash
omega-absorb reports
omega-absorb write-reports --output-dir generated/reports
omega-absorb release-intel
omega-absorb changelog-plus
omega-absorb ci-plan
```

## Tests

```bash
python examples/omega_absorb_poly_prof_v19_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v19.py
```

## v2.0 next targets

1. package layout v2;
2. report bundle contract;
3. workflow seed;
4. CLI command groups;
5. Omega Absorb OS v2.0 docs.
