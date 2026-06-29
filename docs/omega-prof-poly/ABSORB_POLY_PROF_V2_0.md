# Omega Absorb Poly Prof v2.0

Status: Omega Absorb OS v2.0.

## Purpose

v2.0 turns Omega Absorb into a local operating layer with package layout, report bundle contract, workflow seed, command groups and an OS summary object.

```text
source + graph + twin + oak + reports
-> package layout v2
-> report bundle contract
-> workflow seed
-> CLI command groups
-> Omega Absorb OS v2
```

## New modules

- `package_layout_v2.py`
- `report_bundle_contract.py`
- `workflow_seed.py`
- `cli_command_groups.py`
- `omega_absorb_os_v2.py`

## CLI commands

```bash
omega-absorb layout-v2
omega-absorb report-contract
omega-absorb workflow-seed
omega-absorb command-groups
omega-absorb absorb-os
```

## Tests

```bash
python examples/omega_absorb_poly_prof_v20_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v20.py
```

## v2.1 next targets

1. physical package folders;
2. compatibility shims;
3. workflow YAML generator;
4. report bundle validator;
5. command group help renderer.
