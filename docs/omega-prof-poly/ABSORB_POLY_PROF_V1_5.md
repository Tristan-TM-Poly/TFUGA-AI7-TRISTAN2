# Omega Absorb Poly Prof v1.5

Status: tensor, twin, bridge, action and manifest upgrade.

## Purpose

v1.5 adds a local routing layer over public/demo metadata.

```text
ResearchAtoms
-> ProfessorGenomes
-> ProfessorTensors
-> PolyResearchTwin v2
-> DepartmentBridgeOptimization
-> TopNextActions
-> OAKPacketManifest
```

## New modules

- `professor_tensor.py`
- `poly_research_twin_v2.py`
- `department_bridge_optimizer.py`
- `next_actions_engine.py`
- `oak_packet_manifest.py`

## CLI commands

```bash
omega-absorb tensor --source combined
omega-absorb twin-v2 --source combined
omega-absorb bridge-opt --source combined
omega-absorb next-actions --source combined
omega-absorb oak-manifest --source combined
```

## Generated examples

- `generated/omega_absorb_poly_prof_v15/README.md`
- `generated/omega_absorb_poly_prof_v15/professor_tensor.md`
- `generated/omega_absorb_poly_prof_v15/twin_v2.md`
- `generated/omega_absorb_poly_prof_v15/bridge_optimization.md`
- `generated/omega_absorb_poly_prof_v15/next_actions.md`
- `generated/omega_absorb_poly_prof_v15/oak_manifest.json`

## Tests

```bash
python examples/omega_absorb_poly_prof_v15_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v15.py
```

## v1.6 next targets

1. adapter router;
2. source-specific OAK policies;
3. local JSON ingestion pipeline v2;
4. packet writer for top actions;
5. generated GitHub work packet bundle.
